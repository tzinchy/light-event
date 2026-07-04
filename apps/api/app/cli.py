"""Операторские команды: python -m app.cli grant-admin admin@example.com

Назначение первого администратора — операция оператора сервера,
никаких сид-данных (skill real-data-only).
"""

import argparse
import asyncio
import sys

from sqlalchemy import update

from app.core.config import get_settings
from app.core.db import create_engine, create_session_factory
from app.user.models import PlatformRole, User


async def grant_admin(email: str, database_url: str | None = None) -> bool:
    engine = create_engine(database_url or get_settings().database_url)
    session_factory = create_session_factory(engine)
    async with session_factory() as session:
        result = await session.execute(
            update(User).where(User.email == email).values(platform_role=PlatformRole.admin)
        )
        await session.commit()
    await engine.dispose()
    return result.rowcount > 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    grant = sub.add_parser("grant-admin", help="выдать пользователю platform_role=admin")
    grant.add_argument("email", help="e-mail входа пользователя")
    args = parser.parse_args()

    if args.command == "grant-admin":
        if asyncio.run(grant_admin(args.email)):
            print(f"{args.email} — теперь администратор")
        else:
            print(f"Пользователь {args.email} не найден — сначала войдите этой почтой", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
