"""
Импорт выгрузок всех активных поставщиков. Запускается по расписанию раз в час.

Запуск: python -m scripts.sync_suppliers
Код выхода 1, если хотя бы одна выгрузка не загрузилась.
"""

import asyncio
import sys

from app.core.database import AsyncSessionLocal
from app.services.supplier_service import SupplierService


async def main() -> int:
    async with AsyncSessionLocal() as db:
        results = await SupplierService(db=db).sync_all()

    failed = 0
    for result in results:
        if result.ok:
            print(f"{result.supplier.name}: {result.supplier.last_sync_summary}")
        else:
            failed += 1
            print(f"{result.supplier.name}: ошибка, {result.error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
