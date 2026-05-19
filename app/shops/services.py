from decimal import Decimal
from typing import Iterable

from django.db import transaction

from .models import DiscountNotification, PriceHistory, Product, Store


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
