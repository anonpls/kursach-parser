from celery import shared_task

from .services import upsert_products


@shared_task
def sync_dicentre(items: list[dict]) -> int:
    return upsert_products("DiCENTRE", "https://dicentre.ru/", items)


@shared_task
def sync_techprom(items: list[dict]) -> int:
    return upsert_products("TechProm", "https://www.techprom.ru/", items)
