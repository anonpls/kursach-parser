from celery import shared_task

from .services import upsert_products


@shared_task
def sync_dns(items: list[dict]) -> int:
    return upsert_products("DNS", "https://www.dns-shop.ru/", items)


@shared_task
def sync_citilink(items: list[dict]) -> int:
    return upsert_products("Ситилинк", "https://www.citilink.ru/", items)
