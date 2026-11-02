"""
Создаёт сотрудника. Пароль спрашивается в терминале и в историю команд не попадает.

Запуск: python -m scripts.create_user --login admin --name "Имя" --role admin
"""

import argparse
import asyncio
import getpass
import sys

from fastapi import HTTPException

from app.core.database import AsyncSessionLocal
from app.enums.role import UserRoleEnum
from app.services.auth_service import AuthService

MIN_PASSWORD_LENGTH = 10


async def main() -> None:
    parser = argparse.ArgumentParser(description="Создать сотрудника")
    parser.add_argument("--login", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument(
        "--role", choices=[role.value for role in UserRoleEnum], default=UserRoleEnum.manager.value
    )
    args = parser.parse_args()

    password = getpass.getpass("Пароль: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов")
    if password != getpass.getpass("Повторите пароль: "):
        sys.exit("Пароли не совпадают")

    async with AsyncSessionLocal() as db:
        try:
            user = await AuthService(db=db).create_user(
                login=args.login, password=password, name=args.name, role=args.role
            )
        except HTTPException:
            sys.exit("Такой логин уже есть")
    print(f"Создан {user.role.value} {user.login}")


if __name__ == "__main__":
    asyncio.run(main())
