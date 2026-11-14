"""
Импорт выгрузок всех активных поставщиков и докачка фото. Запускается по расписанию раз в час.

Запуск: python -m scripts.sync_suppliers [--photos N]
--photos: сколько фото скачать за запуск, по умолчанию 1500. 0 — не качать.
Код выхода 1, если хотя бы одна выгрузка не загрузилась.
"""

import argparse
import asyncio
import sys

from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.services.partner_catalog_service import PartnerCatalogService
from app.services.supplier_service import SupplierService

# Первый запуск качает фото долго: следующий запуск cron не должен идти параллельно
LOCK_ID = 970_001
DEFAULT_PHOTO_LIMIT = 1500


async def main(photo_limit: int) -> int:
    async with AsyncSessionLocal() as lock_db:
        locked = await lock_db.scalar(text("SELECT pg_try_advisory_lock(:id)"), {"id": LOCK_ID})
        if not locked:
            print("Предыдущий импорт ещё идёт, пропускаю запуск")
            return 0
        try:
            return await run(photo_limit)
        finally:
            await lock_db.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": LOCK_ID})


async def run(photo_limit: int) -> int:
    async with AsyncSessionLocal() as db:
        results = await SupplierService(db=db).sync_all()

    failed = 0
    for result in results:
        if result.ok:
            print(f"{result.supplier.name}: {result.supplier.last_sync_summary}")
        else:
            failed += 1
            print(f"{result.supplier.name}: ошибка, {result.error}", file=sys.stderr)

    if photo_limit > 0:
        async with AsyncSessionLocal() as db:
            saved, not_loaded = await PartnerCatalogService(db=db).fill_missing_photos(limit=photo_limit)
        if saved or not_loaded:
            print(f"Фото: сохранено {saved}, не скачалось {not_loaded}")
    return 1 if failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--photos", type=int, default=DEFAULT_PHOTO_LIMIT)
    sys.exit(asyncio.run(main(photo_limit=parser.parse_args().photos)))
