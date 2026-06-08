import subprocess
import sys
from pathlib import Path

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Min, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import DiscountNotification, Product, Store
from .tasks import parse_and_sync_prices

ROOT_DIR = Path(__file__).resolve().parents[2]
AVAILABLE_STORES = {
    "dicentre": "DiCENTRE",
    "techprom": "TechProm",
}


def dashboard(request):
    query = request.GET.get("q", "").strip()
    store_id = request.GET.get("store", "").strip()
    products = Product.objects.select_related("store").order_by("name")

    if query:
        products = products.filter(Q(name__icontains=query) | Q(store__name__icontains=query))
    if store_id.isdigit():
        products = products.filter(store_id=int(store_id))

    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "available_stores": AVAILABLE_STORES,
        "discounts": DiscountNotification.objects.select_related("product", "product__store").order_by("-created_at")[:8],
        "page_obj": page_obj,
        "products_count": Product.objects.count(),
        "query": query,
        "selected_store": store_id,
        "stores": Store.objects.annotate(products_count=Count("products")).order_by("name"),
        "min_price": Product.objects.aggregate(value=Min("current_price"))["value"],
        "notifications_count": DiscountNotification.objects.count(),
    }
    return render(request, "shops/dashboard.html", context)


def product_detail(request, product_id: int):
    product = get_object_or_404(Product.objects.select_related("store"), id=product_id)
    history = product.price_history.order_by("-created_at")[:30]
    notifications = product.notifications.order_by("-created_at")[:10]
    return render(
        request,
        "shops/product_detail.html",
        {
            "product": product,
            "history": history,
            "notifications": notifications,
        },
    )


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


@require_POST
def run_parser(request):
    selected_stores = [store for store in request.POST.getlist("stores") if store in AVAILABLE_STORES]
    stores = selected_stores or sorted(AVAILABLE_STORES)
    skip_parse = request.POST.get("skip_parse") == "on"
    allow_empty = request.POST.get("allow_empty") == "on"

    try:
        task = parse_and_sync_prices.delay(stores, skip_parse=skip_parse, allow_empty=allow_empty)
    except Exception as exc:
        command = [sys.executable, "scripts/load_prices.py", *stores]
        if skip_parse:
            command.append("--skip-parse")
        if allow_empty:
            command.append("--allow-empty")
        subprocess.Popen(command, cwd=ROOT_DIR)
        messages.warning(
            request,
            "Celery/Redis сейчас недоступен, поэтому парсинг запущен отдельным фоновым процессом. "
            f"Причина: {exc}",
        )
    else:
        messages.success(request, f"Парсинг запущен в Celery. Task ID: {task.id}")

    return redirect("dashboard")
