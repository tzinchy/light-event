# PLAN.md — «light-event»: платформа найма временного персонала

Монорепозиторий production-grade. Работа строго по TDD, только реальные данные, UUIDv7, деньги в копейках, RBAC. Референс — `Платформа найма - standalone.html` (извлечён и разобран: все экраны, статусы, поля, тексты).

---

## 0. Решённые вопросы

1. **Судьба текущего `src/`** — РЕШЕНО (подтверждено): старый каркас домена «hotel» (litestar, почти пустые модели) удаляется вместе с `alembic/` и litestar-зависимостью; backend поднимается заново в `apps/api/`. История остаётся в git.
2. **Имя пакета** — репозиторий называется `hotel-litestar`, проект — `light-event`. Python-пакет именуем `light_event_api` (папку репозитория не трогаю).

Остальные решения приняты и обоснованы ниже — если против, скажи до «go».

---

## 1. Ключевые решения

### 1.1 Карта: MapLibre GL JS + OpenStreetMap (не Yandex)

- **Без API-ключа и биллинга**: OSM-тайлы + MapLibre полностью открыты; Yandex Maps JS API требует ключ, имеет лимиты бесплатного тарифа и запрещает кеширование данных.
- **Тестируемость**: MapLibre работает в Playwright без внешних аккаунтов; e2e не зависят от доступности стороннего SDK.
- **Референс не требует Яндекса**: в дизайне карта — это лента с пинами цен (`pay`, `urgent`), никакого маршрутизирования/панорам.
- Компонент карты изолируем (`MapProvider` interface): если позже понадобится Яндекс (лучший геокодинг по РФ) — заменяется одним адаптером. Геокодинг адресов на MVP не автоматизируем: менеджер ставит точку на карте при создании события (lat/lon сохраняем).

### 1.2 Прочее

- **JS-workspaces**: pnpm workspaces (`apps/web`, `packages/shared-types`). Python — uv (`apps/api`).
- **OpenAPI → TS**: `@hey-api/openapi-ts` генерирует типобезопасный клиент в `packages/shared-types` из схемы FastAPI (команда в CI и Makefile).
- **UUIDv7**: ~~библиотека `uuid_utils`, генерация в Python-коде~~ **ПЕРЕСМОТРЕНО 2026-07-03 (решение заказчика)**: генерация на стороне БД нативной функцией `uuidv7()` PostgreSQL 18 (`server_default`), библиотека `uuid_utils` и `app/core/ids.py` удаляются. Детали — §10.1; skill `uuid-v7-keys` и CLAUDE.md обновить в том же коммите.
- **Деньги**: `BIGINT` копейки везде (`*_kop`). Тарифы в конфиге: публикация смены `99_000` коп (990 ₽), тест компании `150_000` коп (1 500 ₽), комиссия платформы `6%` (из референса).
- **VIP-привилегии** — конфиг/фича-флаги (`vip_boost_in_ranking`, `vip_early_access_minutes`, `vip_priority_support`), не хардкод.
- **Чат**: FastAPI WebSocket + Postgres-хранение; онлайн-статус и подписки на треды через Redis pub/sub (переживает несколько воркеров API).
- **OTP**: Redis, TTL 5 мин, rate-limit на телефон и IP. В dev/test SMS-провайдер за интерфейсом `SmsProvider` (в тестах — перехват кода через интерфейс, не фейковые пользователи). «Яндекс ID» — интерфейс `OAuthProvider`, реализация отложена. **Дополнено 2026-07-03**: телефон остаётся обязательным логином; добавляется подтверждение email кодом через бесплатный SMTP (Brevo, 300 писем/день) — §10.2.
- **Шифрование KYC**: объекты документов в приватном хранилище, ключи объектов не выдаются наружу; контент отдаётся только через API-эндпоинт с проверкой прав (владелец | admin). Компания видит **только статус**.
- **Storage-фолбэк** (решение подтверждено): слой хранения за интерфейсом `Storage` — S3/MinIO основной backend; при `storage_backend=auto` и недоступном S3 на старте автоматически создаётся локальная папка (`var/storage`) и файлы хранятся в ней. Из-за фолбэка загрузка/выдача файлов идёт через API (multipart + стриминг), а не presigned URL — заодно проверка прав всегда в приложении.

---

## 2. Структура монорепо

```
/apps
  /api                    # FastAPI (Python 3.12, uv)
    /app
      /core               # config, db session, security, deps, ledger-примитивы, s3, redis, sms/oauth интерфейсы
      /user  /company  /filial  /team  /invite
      /vacancy  /application  /candidate_list
      /test  /balance  /document  /chat
      /review  /complaint  /admin  /auth
      main.py
    /tests                # зеркалит app/<entity>/, testcontainers
    alembic/  alembic.ini  pyproject.toml  Dockerfile (alpine)
  /web                    # Next.js App Router, TS, shadcn/ui, Tailwind, mobile-first
    /app  (роуты — см. §5)
    /components  /lib
    Dockerfile (alpine)
/packages
  /shared-types           # сгенерированный OpenAPI TS-клиент
/infra
  docker-compose.yml      # postgres:alpine, redis:alpine, minio, api, web, nginx
  docker-compose.test.yml
  /nginx                  # / → web, /api → api, /ws → api (upgrade)
PLAN.md  README.md  Makefile  pnpm-workspace.yaml
```

Слои backend (skill `backend-structure`): `router.py` (тонкий) → `service.py` (логика, транзакции) → `repo.py` (только SQLAlchemy). Миграции — только `alembic revision --autogenerate` / `upgrade head`, никакого `create_all` (включая тесты — тесты применяют миграции).

---

## 3. Доменная модель

PK везде `<entity>_uuid UUID v7`, FK — `<referenced>_uuid`. Все таблицы: `created_at`, `updated_at`. Архивация — статус/флаг, не удаление.

### 3.1 Пользователи и доступ

**user** — `user_uuid`, `phone` (uniq), `name`, `city`, `avatar_key` (S3), `platform_role` (`user | vip_user | admin`), `rating` (агрегат из отзывов), `shifts_done`, `reliability_pct`, `desired_roles[]` (из каталога: Официант, Бариста, Хостес, Бармен, Повар, Ресепшн, Гардероб, Промоутер), `telegram_username`, `telegram_linked`, `is_active`.

**company** — `company_uuid`, `name`, `status` (`pending | verified`), `rating`, `events_count` (агрегаты), `description`.

**filial** — `filial_uuid`, `company_uuid`, `name`, `address`, `lat`, `lon`.

**team_member** (связь user↔company) — `team_member_uuid`, `user_uuid`, `company_uuid`, `filial_uuid` (nullable = все филиалы), `company_role` (`main_manager | manager | coordinator | staff`), `perm_create`, `perm_hire`, `perm_finance`, `perm_invite` (bool; у `main_manager` всегда все true, переключатели заблокированы — как в референсе), `email`.

**invite_link** — `invite_link_uuid`, `company_uuid`, `filial_uuid?`, `company_role`, `code` (uniq, `light-event.app/join/<code>`), `expires_at` (24ч/7д/30д), `max_uses`, `uses_count`, `revoked_at?`, `created_by_uuid`. Переход по ссылке = вступление в команду с ролью.

**favorite_company** — `user_uuid` + `company_uuid` (подписка на уведомления о новых сменах).

### 3.2 Смены и найм

**vacancy** — `vacancy_uuid`, `company_uuid`, `filial_uuid`, `created_by_uuid` (team_member), `role_name`, `event_title`, `starts_at`, `ends_at`, `venue_address`, `lat`, `lon`, `pay_hour_kop`, `pay_total_kop`, `slots`, `urgent`, `tags[]`, `requirements[]`, `status` (`draft → pending_moderation → active → done`, ветка `rejected`; `archived_at`). Публикация: атомарно — списание 990 ₽ с баланса компании + создание заявки на модерацию.

**application** — `application_uuid`, `vacancy_uuid`, `user_uuid`, `status` (`review → confirmed | reserve → paid → done`), `archived_at?`. Таймлайн — таблица **application_event** (`application_event_uuid`, `application_uuid`, `kind` (`applied | confirmed | shift | payout`), `occurred_at`, `actor_uuid`) — ровно 4 шага таймлайна из референса + расширяемо.

**candidate_list_entry** — `entry_uuid`, `company_uuid`, `user_uuid`, `list` (`shortlist | reserve | blacklist`), `note`. Blacklist скрывает соискателя из всех откликов компании (фильтр в repo-слое, тест на это обязателен).

### 3.3 Тесты

**test** — `test_uuid`, `title`, `topic`, `kind` (`platform | company`), `company_uuid?`, `min_correct`, `price_kop?` (для company: 1 500 ₽), `status` (`draft → pending_moderation → published`, ветка `rejected`; platform-тесты создаёт admin сразу в published).

**test_question** — `test_question_uuid`, `test_uuid`, `position`, `text`, `multi` (bool), `options` (jsonb: [{text}]), `correct_indices[]`. Ответы наружу без `correct_indices`.

**test_attempt** — `test_attempt_uuid`, `test_uuid`, `user_uuid`, `status` (`in_progress | finished | abandoned`), `correct_count`, `score_pct`, `passed`, `started_at`, `finished_at?`, `cooldown_until?`. Выход без завершения → `abandoned`, прогресс 0, `cooldown_until = now + TTL` (конфиг, в референсе «15:00»). Пройденный company-тест = бейдж «Тест компании пройден» в карточке отклика.

### 3.4 Деньги (skill money-ledger)

**account** — `account_uuid`, `owner_type` (`company | user | platform`), `owner_uuid`, `available_kop`, `on_hold_kop` (`total = available + on_hold` — вычисляется). Балансы — денормализованный кэш поверх журнала, сверяемый в тестах.

**ledger_entry** — `ledger_entry_uuid`, `debit_account_uuid`, `credit_account_uuid`, `amount_kop > 0`, `kind` (`topup | vacancy_fee | test_fee | hold | release | payout | commission`), `ref_type/ref_uuid` (вакансия/тест/выплата/пополнение), `comment`. Append-only (без UPDATE/DELETE), двойная запись, всё в одной транзакции БД с `SELECT ... FOR UPDATE` по счетам.

**topup_request** — `topup_request_uuid`, `account_uuid`, `amount_kop`, `proof_document_uuid` (пруф платежа в S3), `payment_details`, `status` (`pending → approved | rejected`), `reviewed_by_uuid?`, `reviewed_at?`. Approve = атомарное зачисление через ledger. Внешнего провайдера нет; слой за интерфейсом `PaymentProvider`.

**payout** — `payout_uuid`, `vacancy_uuid`, `company_uuid`, `workers_count`, `amount_kop`, `status` (`pending → processing → paid`), `submitted_at`. Средства на `on_hold` при подтверждении смены; админ «проводит выплату» → списание с on_hold, выплаты соискателям, комиссия 6% платформе.

### 3.5 Документы и KYC (skill s3-documents-kyc)

**document** — `document_uuid`, `owner_uuid` (user или company), `kind` (`passport | selfie_with_passport | medbook | diploma | payment_proof`), `s3_key`, `mime`, `size`, `status` (`pending → verified | rejected`; «missing» = отсутствие записи), `reviewed_by_uuid?`, `reject_reason?`, `flag` (авто-пометка для очереди, напр. «требует ручной проверки»). Доступ к содержимому: только владелец и admin (presigned URL). Компания — только статусы.

### 3.6 Чат

**chat_thread** — `chat_thread_uuid`, `application_uuid` (тред на заявку), участники: соискатель + команда компании. **chat_message** — `chat_message_uuid`, `chat_thread_uuid`, `sender_uuid`, `text`, `sent_at`, `read_at?`. Непрочитанные — по `read_at`; онлайн — Redis (TTL-ключ по соединению).

### 3.7 Отзывы, жалобы, модерация

**review** — `review_uuid`, `author_type/author_uuid`, `target_type/target_uuid` (user | company), `vacancy_uuid`, `rating` 1–5, `text`, `kind` (`about_org | about_event | about_worker`). Один отзыв на пару (автор, заявка). Рейтинги user/company — агрегаты.

**complaint** — `complaint_uuid`, `author_...`, `target_...`, `vacancy_uuid?`, `kind` (напр. «Задержка оплаты», «Неявка на смену»), `severity` (`low | medium | high`), `text`, `status` (`open → resolved | dismissed`).

**Очередь модерации админа** — не отдельная таблица, а union pending-объектов: `vacancy(pending_moderation)`, `test(pending_moderation)`, `topup_request(pending)`, `document(pending)`, `payout(pending)` — единый эндпоинт-агрегатор для админки.

### 3.8 Auth

OTP-коды и сессии — Redis (не Postgres): `otp:{phone}` TTL 5 мин + счётчик попыток; JWT access (короткий) + refresh в Redis с ревокацией. Регистрация = первый вход по телефону; далее шаг KYC (загрузка 3 документов + чекбокс согласия на ПДн — сохраняем `pd_consent_at`).

---

## 4. Роли и матрица доступа (skill rbac-permissions)

| Действие | user | vip | staff | coordinator | manager | main_manager | admin |
|---|---|---|---|---|---|---|---|
| Лента/отклик/тесты/чат/профиль | ✅ | ✅ (буст выдачи, ранний доступ) | — | — | — | — | — |
| Создать/опубликовать событие | — | — | по `perm_create` | по `perm_create` | по `perm_create` | ✅ | — |
| Нанимать (confirm/reserve/шортлист/ЧС) | — | — | по `perm_hire` | по `perm_hire` | по `perm_hire` | ✅ | — |
| Баланс, пополнение, операции | — | — | по `perm_finance` | по `perm_finance` | по `perm_finance` | ✅ | — |
| Инвайт-ссылки, права команды | — | — | по `perm_invite` | по `perm_invite` | по `perm_invite` | ✅ (права выдаёт только он) | — |
| Модерация (заявки/KYC/платежи/жалобы) | — | — | — | — | — | — | ✅ |
| Содержимое KYC-документов | владелец | владелец | ❌ | ❌ | ❌ | ❌ | ✅ |

Каждый защищённый эндпоинт — зависимость `require_permission(...)`; на каждую клетку «❌» — негативный тест.

---

## 5. Карта экранов (из референса) → роуты Next.js

**Лендинг `/`** — hero (счётчик смен, CTA «Стать сотрудником»/«Для организаций»), превью 3 смен, «Как это работает», фичи (отклик в один тап / проверенные профили / рейтинг), CTA-band. Гость видит ленту, но контакты/отклик — под логином.

**Auth `/auth`** — welcome (вход по телефону, «Войти через Яндекс ID» — заглушка за интерфейсом) → phone → otp (6 ячеек, resend-таймер) → kyc (3 карточки загрузки: паспорт-разворот, селфи с паспортом, медкнижка; чекбокс согласия). Степпер «Телефон → Код → Верификация».

**Кабинет соискателя `/w/...`** (mobile-first, нижний таб-бар: Лента / Заявки / Чат / Тесты / Профиль):
- `feed` — список/карта (сегмент-переключатель), карточка: роль, org+рейтинг, событие, дата/время, дистанция, ₽/час, теги, срочно, filled/slots + прогресс, ♥ избранное; карта — пины с ценой.
- `shift/[uuid]` — детали: О событии, Требования, контакты (скрыты для гостя), «Откликнуться» / «Отклик отправлен» / «Вы в резерве», чат с организатором, итог за смену.
- `apps` + `apps/[uuid]` — мои заявки со статус-бейджами, карточка заявки с таймлайном (Отклик → Подтверждение → Смена → Выплата), «Оставить отзыв» (после paid/done), «Открыть чат заявки». Пусто → «Пока нет заявок».
- `tests` — платформенные и тесты компаний (бейдж), passed + score%, «Пройти/Пройти заново», cooldown («Повтор через …», кнопка заблокирована), прохождение: одиночный/multi выбор («Выберите все верные варианты»), прогресс-бар, подтверждение выхода, экран результата (кольцо score, порог 70%).
- `chat` + `chat/[uuid]` — треды (аватар, последнее, время, непрочитанные, онлайн), переписка, отправка.
- `profile` + `profile/edit` — шапка (рейтинг, смены, надёжность, уровень), Документы и статусы (verified/pending/missing), Мои тесты, Отзывы, Избранные компании, Telegram (привязать/отвязать), редактирование (имя/телефон/город/фото, чипсы желаемых ролей).
- `review` — звёзды + текст → отправка.

**Кабинет организации `/org/...`** (desktop-сайдбар, адаптив):
- `dashboard` — 4 стата (Заполняемость, Средний рейтинг, Активные события, Расходы за месяц), бар-чарт недели.
- `branches`/`events` — карточки филиалов (актив. смен, событий), фильтры по филиалу и статусу (Все/Активные/Черновики), строки событий: title, филиал, дата, роль×кол-во, filled/slots + прогресс, расход, статус-бейдж (Активно/Черновик/Завершено). Завершённые → архив.
- `create` — чипсы роли, филиал, дата/время, слоты (степпер), ставка ₽/час + автоитог, блок оплаты: «Публикация смены 990 ₽ — спишется со счёта организации», «Оплатить и опубликовать» → «Оплачено · отправлено на модерацию администратора».
- `candidates` — фильтры «Все / Лучшие / Резерв / ЧС» со счётчиками, строка кандидата (рейтинг, смен, надёжность%, дистанция, отклик N мин назад, пометки, топ-бейдж), детальная карточка: паспорт/медкнижка/тест ✓/✗, бейдж «Тест компании пройден», кнопки «Нанять/Нанят», «В резерв», «В чёрный список» (+ «Скрыт из откликов на все ваши события»), «Пригласить».
- `tests` — список тестов (Базовый/Тест компании, N вопросов, прохождения), «Создать тест — 1 500 ₽» → оплата → модерация.
- `team` — таблица: сотрудник, email, филиал, роль-бейдж (Главный менеджер/Менеджер/Координатор), 4 переключателя прав (у главного — залочены «Полный доступ»); Пригласительные ссылки: роль + срок (24ч/7д/30д) → генерация `join/<code>`, список ссылок (переходы X/Y, истекает, Копировать/Отозвать).
- `balance` — Доступно / В резерве под выплаты / Всего; «Пополнить» (окно заявки: сумма + пруф → на подтверждение админу); Операции по счёту (выплата/пополнение/комиссия 6%, суммы моно-шрифтом); «Выплаты к проведению».
- `reviews` — отзывы о компании и о событиях (звёзды, автор, дата).

**Админка `/admin/...`**: `overview` (Пользователи, KYC%, Оборот, Споры + виджеты очередей), `requests` (Публикация смены / Новый тест компании: оплачено, когда; Одобрить/Отклонить → Опубликовано/Отклонено), `payments` (заявки на пополнение + очередь выплат: организация, событие, N сотрудников, сумма, подана; «Провести выплату»; статусы На этапе оплаты/Обрабатывается/Выплачено), `kyc` (очередь: документ, когда подана, авто-flag; Проверить → просмотр документа → Одобрить/Отклонить), `orgs` (Проверена/На проверке), `reports` (жалобы: кто→на кого, вид, серьёзность, время).

---

## 6. API (FastAPI, префикс `/api/v1`)

- **auth**: `POST /auth/otp/request`, `POST /auth/otp/verify` (→ JWT), `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`.
- **user**: `GET/PATCH /users/me`, `POST /users/me/desired-roles`, `POST/DELETE /users/me/telegram`, `GET/POST/DELETE /users/me/favorites`.
- **document**: `POST /documents` (presigned upload → метаданные), `GET /documents/my`, `GET /documents/{uuid}/content` (owner|admin).
- **company**: `POST /companies`, `GET/PATCH /companies/{uuid}`, `GET /companies/{uuid}/reviews`; **filial**: CRUD `/companies/{uuid}/filials`.
- **team**: `GET /companies/{uuid}/team`, `PATCH /team-members/{uuid}/permissions` (только main_manager), `DELETE /team-members/{uuid}`; **invite**: `POST /companies/{uuid}/invites`, `GET .../invites`, `POST /invites/{code}/accept`, `POST /invites/{uuid}/revoke`.
- **vacancy**: `GET /vacancies` (публичная лента: фильтры geo/роль/дата; пусто = `[]`), `GET /vacancies/{uuid}`, `POST /companies/{uuid}/vacancies` (draft), `POST /vacancies/{uuid}/publish` (списание 990 ₽ + модерация, атомарно), `PATCH`, `POST /vacancies/{uuid}/archive`.
- **application**: `POST /vacancies/{uuid}/applications`, `GET /applications/my`, `GET /applications/{uuid}` (+timeline), `POST /applications/{uuid}/status` (confirm/reserve — по `perm_hire`; ЧС-фильтр), `GET /vacancies/{uuid}/applications`.
- **candidate_list**: `GET /companies/{uuid}/candidates?list=`, `PUT /companies/{uuid}/candidates/{user_uuid}` (shortlist/reserve/blacklist), `DELETE ...`.
- **test**: `GET /tests` (published, для юзера — с его результатами), `POST /companies/{uuid}/tests` (списание 1 500 ₽ + модерация), `POST /tests/{uuid}/attempts`, `POST /attempts/{uuid}/answers`, `POST /attempts/{uuid}/finish`, `POST /attempts/{uuid}/abandon` (→ cooldown).
- **balance**: `GET /companies/{uuid}/account`, `GET .../account/operations`, `POST .../topup-requests` (+пруф), `GET /companies/{uuid}/payouts`.
- **chat**: `GET /chat/threads`, `GET /chat/threads/{uuid}/messages`, `WS /ws/chat` (auth по токену; send/receive/read/online).
- **review**: `POST /reviews` (по завершённой заявке), `GET /users/{uuid}/reviews`.
- **complaint**: `POST /complaints`, `GET /complaints/my`.
- **admin**: `GET /admin/overview`, `GET /admin/requests`, `POST /admin/vacancies/{uuid}/moderate`, `POST /admin/tests/{uuid}/moderate`, `GET /admin/topup-requests`, `POST /admin/topup-requests/{uuid}/resolve`, `GET /admin/payouts`, `POST /admin/payouts/{uuid}/execute`, `GET /admin/kyc-queue`, `POST /admin/documents/{uuid}/moderate`, `GET /admin/companies`, `POST /admin/companies/{uuid}/verify`, `GET /admin/complaints`, `POST /admin/complaints/{uuid}/resolve`.

---

## 7. Инфраструктура и тесты

- `infra/docker-compose.yml`: `postgres:18-alpine`, `redis:alpine`, `minio` (+bucket-init), `api` (uvicorn), `web` (next), `nginx:alpine` (`/` → web, `/api` → api, `/ws` → api с upgrade). `.env.example` под все сервисы. Все Dockerfile — alpine, multi-stage.
- Тесты backend: pytest + testcontainers — реальные Postgres/Redis/MinIO на сессию, миграции `alembic upgrade head` в контейнер, транзакционная изоляция на тест. Фикстуры — только в тестах.
- Frontend: Vitest + Testing Library (компоненты/логика), Playwright e2e против compose-стенда.
- CI-порядок в Makefile/README: `make test-api`, `make test-web`, `make e2e`, `make openapi-client`.

## 8. Дизайн-система (skill shadcn-design-tokens)

shadcn/ui + Tailwind-токены из референса: zinc (`#18181b` текст/инверсия, `#fafafa/#f4f4f5` поверхности, `#e4e4e7` границы, `#52525b/#a1a1aa` вторичный), акцент green (`#16a34a/#15803d`, фон `#f0fdf4`), статусы: amber `#b45309/#fffbeb` (review/draft/pending), blue `#1d4ed8/#eff6ff` (paid/processing), red `#b91c1c/#fef2f2` (rejected/blacklist), фиолетовый `#7c3aed/#f5f3ff` (бейдж «Тест компании»). Шрифты Geist + Geist Mono (суммы/OTP/код). Крупные скругления (8–14px), статус-бейджи, сегмент-контролы, чипсы, степперы, прогресс-бары — как в референсе. Язык — русский, тексты беру из референса (словарь DICT). Демо-строки референса в БД НЕ попадают — пустые состояния честные («Пока нет заявок», «Нет диалогов», «Пока нет избранных…»).

---

## 9. Порядок работы (каждый модуль = red → green → refactor)

**Поправка от 2026-07-02 (решение заказчика): фронтенд не ждёт шага 14, а чередуется.** Сразу после шага 6: Next.js-скелет + дизайн-токены + лендинг + auth-флоу + экраны уже готовых модулей (кабинет организации: команда, инвайты, баланс). Далее каждый backend-модуль закрывается своими экранами до перехода к следующему.

0. **Реструктуризация**: монорепо-скелет, перенос/чистка (`src/` → `apps/api/app/`), pnpm-workspace, `.claude/skills/` — разложить 8 скиллов по каталогам + команда `/new-module`.
1. **TDD-контур**: compose (pg/redis/minio/api/web/nginx), падающий health-check в testcontainers → зелёный; alembic init; первый прогон миграций в тестах.
2. **auth + OTP + KYC-шаг** (Redis OTP, JWT, rate-limit, согласие ПДн).
3. **user + документы + S3** (метаданные, статусы, presigned, запрет доступа).
4. **company + filial + RBAC-ядро** (permission-зависимости, негативные тесты).
5. **team + инвайт-ссылки** (роли, матрица, сроки/лимиты/отзыв ссылки).
6. **balance/ledger** (двойная запись, копейки, блокировки, topup-заявки) — раньше вакансий, т.к. публикация платная.
7. **vacancy**: создание → платная публикация → модерация → лента (гео, фильтры, пустые состояния).
8. **application + candidate_list**: отклики, статусы, таймлайн, шортлист/резерв/ЧС, архив.
9. **tests**: платные тесты компаний, модерация, прохождение, multi, cooldown, бейдж.
10. **payout-цикл**: on_hold, выплаты админом, комиссия 6%.
11. **chat**: WebSocket, треды, непрочитанные, онлайн.
12. **review + complaint**.
13. **admin**: overview-агрегаты, очереди модерации, KYC, организации, жалобы.
14. **Frontend**: токены темы + лендинг + auth → кабинет соискателя (лента/карта MapLibre, смена, заявки, тесты, чат, профиль) → кабинет организации → админка. Vitest по ходу, Playwright e2e на ключевые сценарии (вход, отклик, публикация, модерация, пополнение).
15. **Полировка**: адаптив, пустые состояния, README, e2e-стабилизация.

После каждого модуля — короткий отчёт (сделано/осталось). Скиллы и CLAUDE.md обновляю при уточнении правил.

---

## 10. Итерация 2026-07-03: uuidv7 в БД, email-OTP, e2e, дисциплина коммитов

### 10.0 Дисциплина коммитов (действует сразу)

- **Один коммит = один шаг**: тесты модуля / реализация модуля / миграция / regen SDK (`openapi.json` + `shared-types`) / каждый экран web — отдельными коммитами. Никаких «backend + 4 экрана + референс» одним куском.
- `.DS_Store` → в `.gitignore`, удалить из индекса (`git rm --cached`). HTML-референсы больше не коммитим.

### 10.1 UUIDv7 → генерация в PostgreSQL 18

Везде `postgres:18-alpine` (dev/test compose, testcontainers) — нативная `uuidv7()` доступна.

1. **FIRST TEST**: интеграционный тест — raw `INSERT` в таблицу без указания PK возвращает UUID версии 7.
2. Все модели: `default=uuid7` → `server_default=text("uuidv7()")`; репозитории уже делают `flush()`, PK возвращается через RETURNING (проверено: явных чтений ID до flush нет).
3. Миграция: `alembic revision --autogenerate` (включить `compare_server_default=True` в `env.py`) → `ALTER TABLE … SET DEFAULT uuidv7()`.
4. Удалить `app/core/ids.py` и зависимость `uuid_utils`.
5. Обновить skill `uuid-v7-keys` и пункт 3 «железных правил» CLAUDE.md: «UUIDv7 как PK везде, генерация в БД (`server_default=uuidv7()`, PostgreSQL 18)».
6. Полный прогон pytest — тесты на реальном Postgres поймают любые пропущенные места.

### 10.2 Email-OTP (телефон остаётся обязательным логином)

Email — необязательное поле профиля с подтверждением кодом; вход по-прежнему только по телефону.

- **Провайдер**: `app/core/email.py` — `EmailProvider` (Protocol, симметрично `SmsProvider`) + `SmtpEmailProvider` (aiosmtplib) + `ConsoleEmailProvider` (dev-фолбэк без SMTP-настроек).
- **Прод бесплатно**: Brevo — 300 писем/день, обычный SMTP, только env-переменные (`SMTP_HOST/PORT/USER/PASSWORD/FROM`) в `.env.example`. Никакого SDK.
- **Dev**: сервис **Mailpit** в `infra/docker-compose.yml` (локальный SMTP + веб-просмотр писем + HTTP API).
- **Рефактор**: логика кодов из `AuthService` (rate-limit запросов, TTL, лимит попыток, `compare_digest`) → переиспользуемый `OtpStore` в `app/core/`, ключи `otp:{channel}:{destination}`. Поведение телефонного OTP не меняется — существующие 11 тестов остаются зелёными.
- **API** (user-модуль): `POST /users/me/email` (задать почту + отправить код), `POST /users/me/email/confirm` (код → `email_verified_at`). Смена почты сбрасывает подтверждение.
- **FIRST TEST**: pytest — запрос кода, подтверждение, неверный код, истечение, rate-limit, смена почты сбрасывает флаг.
- **Web**: блок «Почта» в профиле (ввод → код через существующий `otp-input` → бейдж «Подтверждена»), Vitest на логику.
- SMS в проде: остаётся `ConsoleSmsProvider`; когда появится бюджет — реализация `SmsRuProvider` за тем же интерфейсом (SMS.ru, ~4–6 ₽/SMS; бесплатная отправка на свой номер для отладки).

### 10.3 Playwright e2e + добор тестов web

- Каркас: `apps/web/e2e/`, Playwright против compose-test-стенда (`make e2e`).
- Перехват кодов в e2e — только через интерфейсы: email-код читаем из Mailpit HTTP API; для SMS в тестовом стенде — реализация `SmsProvider`, складывающая код в Redis (используется только в test-compose, в prod-конфиге недостижима). Фейковых пользователей/данных нет — real-data-only.
- Первые сценарии: вход по OTP → заполнение профиля → отклик на смену; кабинет организации: создание смены → найм.
- Vitest: добор по существующим экранам — форматирование, статусы заявок, guard'ы ролей в `site-header`.

### 10.4 Регистрация организации через заявку + минимальный admin (решение заказчика 2026-07-03)

Сейчас `POST /companies` создаёт кабинет мгновенно; статус `pending` в модели есть, но ничего не гейтит. Референс подтверждает флоу: админ → «Организации» → список «На проверке» → «Подтвердить».

- **Заявка** (`POST /companies`): название, описание, **ИНН** (10/12 цифр, контрольные числа), **ОГРН** (13/15, контрольная цифра), адрес + **обязательная точка на карте** (lat/lon через MapLibre-пикер), контактный телефон. Статус — `pending`.
- **Pending = полная блокировка**: все эндпоинты кабинета, кроме просмотра собственной заявки, → 403 «Организация на проверке»; в web — экран «Заявка отправлена, ожидайте подтверждения». Существующие компании в dev-БД останутся pending — честно попадут под модерацию.
- **Admin-модуль** (`app/admin/`): `GET /admin/companies?status=pending`, `POST /admin/companies/{uuid}/verify`, `POST /admin/companies/{uuid}/reject` (с причиной, показываем заявителю). Доступ — только `platform_role=admin`, негативные тесты обязательны.
- **Первый админ**: management-команда `uv run python -m app.cli grant-admin <phone>` (операция оператора сервера, не сид-данные). UI-экран `/admin` — список заявок, подтвердить/отклонить.
- **Карта**: подключить MapLibre GL + OSM (§1.1), компонент `MapPicker`; сначала в заявке организации, затем переиспользуем при создании смены и в ленте.
- **FIRST TEST**: невалидные ИНН/ОГРН → 422; заявка без точки на карте → 422; pending-компания публикует/нанимает/пополняет → 403; `verify` админом открывает доступ; `reject` показывает причину; не-админ на admin-эндпоинтах → 403.
- Миграция: поля `company.inn`, `ogrn`, `address`, `lat`, `lon`, `contact_phone`, `status=rejected`, `reject_reason`, `verified_at`.

### 10.5 Порядок и коммиты итерации (приоритет заказчика: тесты API прежде всего)

0. Сделано 2026-07-03 вне очереди: `logging.basicConfig` в `create_app` — OTP-коды видны в консоли dev-сервера.
1. `.gitignore` + чистка индекса — 1 коммит.
2. §10.1 uuidv7: тест → модели+миграция → чистка ids.py → skill+CLAUDE.md — 3–4 коммита.
3. **Добор API-тестов** по тонким модулям: filial (2), user (4), document (5) — негативные RBAC-кейсы, границы rate-limit, KYC-запреты — по коммиту на модуль.
4. §10.4 организация-заявка + admin: тесты → backend → миграция → CLI grant-admin → SDK → MapPicker → экраны заявки и `/admin` — отдельными коммитами.
5. §10.2 email-OTP: тесты `OtpStore`+email → реализация → рефактор auth — 3 коммита; Mailpit/env — 1; SDK — 1; экран профиля — 1–2.
6. §10.3 Playwright — в конец итерации: каркас — 1; каждый сценарий — отдельный коммит.

---

## 11. Итерация 2026-07-04 (автономный режим): замкнуть продуктовый цикл

Правило «ждать go» снято заказчиком — решения фиксируются здесь и выполняются сразу.

### 11.1 Очередь модерации админа (backend, TDD)

`GET /api/v1/admin/requests` — агрегатор pending-объектов (§6): `vacancy(pending_moderation)` + `test(pending_moderation)` с типом, названием, компанией, `paid_at`/`created_at`. Только admin (негативные тесты). Пополнения уже покрыты `GET /admin/topup-requests`.

### 11.2 Админка web: вкладки очередей

`/admin` → вкладки «Организации» (есть) / «Публикации» (вакансии+тесты: Одобрить/Отклонить) / «Пополнения» (approve/reject с суммой). SDK regen после 11.1.

### 11.3 E2E: полный цикл найма

Продолжение org-сценария: пополнение с пруфом → админ зачисляет → «Оплатить и опубликовать» (990 ₽) → админ одобряет публикацию → смена в ленте у соискателя → отклик → «Нанять». Покрывает сценарии §14 (вход, отклик, публикация, модерация, пополнение).

### 11.4 Payout-цикл (§9 п.10, backend TDD)

on_hold при подтверждении смены, `POST /admin/payouts/{uuid}/execute`: выплаты соискателям + комиссия 6% платформе, атомарно через леджер. Затем UI «Выплаты к проведению» в админке и балансе организации.

Порядок коммитов: тест → реализация → SDK → экран → e2e, по шагу на коммит.
