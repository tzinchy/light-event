"""Единая точка импорта всех SQLAlchemy-моделей.

Alembic autogenerate видит только модели, зарегистрированные в Base.metadata,
поэтому каждый новый app/<entity>/models.py импортируется здесь.
"""
