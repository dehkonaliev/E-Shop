from django.core.validators import MinValueValidator
from django.db import models

from baseapp.models import BaseModel


class Cart(BaseModel):
    user = models.OneToOneField(
        "authentication.CustomUser",
        on_delete=models.CASCADE,
        related_name="cart",
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Cart for {self.user}"


class CartItem(BaseModel):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_cart_product",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="cart_item_quantity_positive",
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product}"


class Order(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        SHIPPING = "shipping", "Yetkazilmoqda"
        COMPLETED = "completed", "Bajarildi"
        CANCELLED = "cancelled", "Bekor qilindi"

    user = models.ForeignKey(
        "authentication.CustomUser",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    total_price = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    shipping_address = models.TextField(max_length=1000)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_price__gte=0),
                name="order_total_price_nonnegative",
            )
        ]

    def __str__(self):
        return f"Order {self.uuid} for {self.user}"


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_at_that_time = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(price_at_that_time__gte=0),
                name="order_item_price_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
