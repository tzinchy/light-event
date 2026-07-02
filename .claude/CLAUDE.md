CLAUDE.md — постоянные правила проекта «light-event»

Платформа найма временного персонала для отелей/ресторанов/событий. Монорепо.

Стек (не менять без явного согласования)


Backend: Python + FastAPI, SQLAlchemy 2.x async, Alembic.
БД: PostgreSQL. Кэш/OTP/rate-limit: Redis.
Frontend: React + Next.js (App Router) + TypeScript + shadcn/ui + Tailwind. Mobile-first.
Файлы: S3-совместимое (MinIO в dev); если S3/MinIO недоступен — автоматический фолбэк в локальную папку (var/storage), слой за интерфейсом Storage. Карта: см. PLAN.md.
Тесты: pytest + testcontainers (реальные Postgres/Redis/MinIO), Vitest + Testing Library, Playwright (e2e).
Прокси: Nginx. Все образы — Alpine. docker-compose для dev и для тестов.


Железные правила (нарушать нельзя)


TDD всегда: красный тест → код → рефактор. Нет теста — нет кода. См. skill tdd-workflow.
Только реальные данные: никаких mock/seed/fake в рантайме и dev/prod БД. Нет данных → пустое состояние. См. skill real-data-only.
UUIDv7 как PK везде, генерация в приложении. См. skill uuid-v7-keys.
Деньги — целые копейки, атомарный леджер, пополнение через ручное подтверждение админом. См. skill money-ledger.
RBAC + матрица прав на каждом защищённом эндпоинте. Компания НЕ видит документы KYC. См. skills rbac-permissions, s3-documents-kyc.
Миграции — только Alembic командами (revision --autogenerate, upgrade head), структуру руками не городить, никакого create_all. См. skill backend-structure.
Backend-структура — по сущностям: app/<entity>/ с router.py/service.py/repo.py/schemas.py/models.py. См. skill backend-structure.
Тест пишется ПЕРВЫМ (FIRST TEST), только реальные API/данные.
Локаль по умолчанию — русский.


Роли

user, vip-user, manager, main-manager (владелец кабинета компании), admin.
Права внутри компании: create / hire / finance / invite.

Процесс


Крупные изменения: сначала план в PLAN.md, показать, дождаться "go".
Неоднозначность в требованиях → спросить, не додумывать.