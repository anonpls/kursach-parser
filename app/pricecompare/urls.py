from django.urls import path

from app.shops.views import dashboard, product_detail, product_price_chart, run_parser

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("products/<int:product_id>/", product_detail, name="product_detail"),
    path("api/products/<int:product_id>/chart/", product_price_chart, name="product_price_chart"),
    path("parse/", run_parser, name="run_parser"),
]
