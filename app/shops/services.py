from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import json
import random
from pathlib import Path
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from .models import DiscountNotification, PriceHistory, Product, Store


PRICE_QUANT = Decimal("0.01")


def upsert_products(store_name: str, base_url: str, items: Iterable[dict]) -> int:
    store, _ = Store.objects.get_or_create(name=store_name, defaults={"base_url": base_url})
    updated = 0

    for item in items:
        with transaction.atomic():
            product, created = Product.objects.get_or_create(
                store=store,
                external_id=item["external_id"],
                defaults={
                    "name": item["name"],
                    "url": item["url"],
                    "current_price": Decimal(item["price"]),
                },
            )
            new_price = Decimal(item["price"])

            if created:
                PriceHistory.objects.create(product=product, price=new_price)
                updated += 1
                continue

            if product.current_price != new_price:
                old_price = product.current_price
                product.current_price = new_price
                product.name = item["name"]
                product.url = item["url"]
                product.save(update_fields=["current_price", "name", "url", "updated_at"])
                PriceHistory.objects.create(product=product, price=new_price)

                if new_price < old_price:
                    DiscountNotification.objects.create(
                        product=product,
                        old_price=old_price,
                        new_price=new_price,
                    )
                updated += 1

    return updated


def simulate_price_dynamics(
    stores: Iterable[str] | None = None,
    days: int = 10,
    max_products: int = 40,
    seed: int = 42,
    json_dir: Path | None = None,
) -> dict[str, int]:
    """Create deterministic historical price changes and optional JSON snapshots for demos."""

    if days < 2:
        raise ValueError("days must be at least 2")
    if max_products < 1:
        raise ValueError("max_products must be greater than 0")

    products = Product.objects.select_related("store").order_by("store__name", "id")
    if stores:
        products = products.filter(store__name__in=list(stores))
    selected_products = list(products[:max_products])
    rng = random.Random(seed)
    now = timezone.now()
    snapshots: dict[str, list[list[dict[str, str]]]] = {}
    history_created = 0
    discounts_created = 0

    with transaction.atomic():
        for product in selected_products:
            base_price = Decimal(product.current_price)
            previous_price = product.current_price
            product_snapshots = []

            for day_index in range(days):
                days_ago = days - day_index - 1
                changed_at = now - timezone.timedelta(days=days_ago)
                price = _modeled_price(base_price, product.id, day_index, rng)
                history = PriceHistory.objects.create(product=product, price=price)
                PriceHistory.objects.filter(id=history.id).update(created_at=changed_at)
                history_created += 1

                if day_index > 0 and price < previous_price:
                    notification = DiscountNotification.objects.create(
                        product=product,
                        old_price=previous_price,
                        new_price=price,
                    )
                    DiscountNotification.objects.filter(id=notification.id).update(created_at=changed_at)
                    discounts_created += 1

                previous_price = price
                product_snapshots.append(
                    {
                        "external_id": product.external_id,
                        "name": product.name,
                        "url": product.url,
                        "price": str(price),
                    }
                )

            product.current_price = previous_price
            product.save(update_fields=["current_price", "updated_at"])
            snapshots.setdefault(product.store.name, [[] for _ in range(days)])
            for index, item in enumerate(product_snapshots):
                snapshots[product.store.name][index].append(item)

    if json_dir:
        _write_simulated_snapshots(json_dir, snapshots, now, days)

    return {
        "products": len(selected_products),
        "history": history_created,
        "discounts": discounts_created,
        "json_files": sum(len(store_snapshots) for store_snapshots in snapshots.values()) if json_dir else 0,
    }


def _modeled_price(base_price: Decimal, product_id: int, day_index: int, rng: random.Random) -> Decimal:
    direction = -1 if (product_id + day_index) % 3 == 0 else 1
    percent = Decimal(str(rng.randint(2, 18))) / Decimal("100")
    wobble = Decimal(str(((product_id + day_index) % 5) - 2)) / Decimal("100")
    multiplier = Decimal("1") + (percent * direction) + wobble
    price = base_price * multiplier
    if price < Decimal("1"):
        price = Decimal("1")
    return price.quantize(PRICE_QUANT, rounding=ROUND_HALF_UP)


def _write_simulated_snapshots(
    json_dir: Path,
    snapshots: dict[str, list[list[dict[str, str]]]],
    now,
    days: int,
) -> None:
    json_dir.mkdir(parents=True, exist_ok=True)
    for store_name, store_snapshots in snapshots.items():
        safe_store_name = store_name.lower().replace(" ", "_")
        for index, items in enumerate(store_snapshots):
            snapshot_date = (now - timezone.timedelta(days=days - index - 1)).date().isoformat()
            output_path = json_dir / f"{safe_store_name}_{snapshot_date}.json"
            output_path.write_text(
                json.dumps(items, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
