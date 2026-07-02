"""Единая точка импорта всех SQLAlchemy-моделей.

Alembic autogenerate видит только модели, зарегистрированные в Base.metadata,
поэтому каждый новый app/<entity>/models.py импортируется здесь.
"""

import app.application.models  # noqa: F401
import app.balance.models  # noqa: F401
import app.candidate_list.models  # noqa: F401
import app.company.models  # noqa: F401
import app.document.models  # noqa: F401
import app.filial.models  # noqa: F401
import app.invite.models  # noqa: F401
import app.team.models  # noqa: F401
import app.user.models  # noqa: F401
import app.vacancy.models  # noqa: F401
