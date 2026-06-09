from celery import shared_task

from .services import upsert_products


@shared_task
def sync_dicentre(items: list[dict]) -> int:
    return upsert_products("DiCENTRE", "https://dicentre.ru/", items)


@shared_task
def sync_techprom(items: list[dict]) -> int:
    return upsert_products("TechProm", "https://www.techprom.ru/", items)


@shared_task
def parse_and_sync_prices(
    stores: list[str] | None = None,
    skip_parse: bool = False,
    allow_empty: bool = False,
    max_pages: int = 1,
) -> dict:
    from scripts.load_prices import SPIDERS, parse_prices, save_prices

    selected_stores = stores or sorted(SPIDERS)
    if not skip_parse:
        parse_prices(selected_stores, max_pages=max_pages)
    save_prices(selected_stores, allow_empty=allow_empty)
    return {"stores": selected_stores, "skip_parse": skip_parse, "allow_empty": allow_empty, "max_pages": max_pages}
