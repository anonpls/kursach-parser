from django.db import models


class Store(models.Model):
    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField()

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    external_id = models.CharField(max_length=200)
    name = models.CharField(max_length=255)
    url = models.URLField()
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="UAH")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("store", "external_id")

    def __str__(self) -> str:
        return f"{self.name} ({self.store.name})"


class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_history")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class DiscountNotification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="notifications")
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
