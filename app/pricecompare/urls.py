from django.urls import path

from shops.views import product_price_chart

urlpatterns = [
    path("api/products/<int:product_id>/chart/", product_price_chart, name="product_price_chart"),
]
