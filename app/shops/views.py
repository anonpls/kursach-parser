from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Product


def product_price_chart(request, product_id: int):
    product = get_object_or_404(Product, id=product_id)
    points = [
        {"date": entry.created_at.isoformat(), "price": float(entry.price)}
        for entry in product.price_history.order_by("created_at")
    ]
    return JsonResponse(
        {
            "product": product.name,
            "store": product.store.name,
            "points": points,
        }
    )
