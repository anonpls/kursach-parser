from celery import shared_task

from .services import upsert_products


@shared_task
def sync_rozetka(items: list[dict]) -> int:
    return upsert_products("ROZETKA", "https://rozetka.com.ua/", items)


@shared_task
def sync_citrus(items: list[dict]) -> int:
    return upsert_products("Citrus", "https://www.ctrs.com.ua/", items)
