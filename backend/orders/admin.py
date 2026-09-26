from decimal import Decimal

from django.contrib import admin
from django.db.models import Count, F, Sum
from rest_framework.exceptions import ValidationError

from .models import Cart, CartItem, Order, OrderItem
from .services import update_order_status


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["product", "product_name", "quantity", "price_at_that_time", "line_total"]
    readonly_fields = ["product", "product_name", "line_total"]
    autocomplete_fields = ["product"]
    can_delete = False
    verbose_name_plural = "Order items"

    @admin.display(description="Line total")
    def line_total(self, obj):
        if not obj.pk:
            return "—"
        return (obj.price_at_that_time * obj.quantity).quantize(Decimal("0.01"))


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "user",
        "status",
        "item_count",
        "total_price",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["user__username", "user__email", "shipping_address", "uuid"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    list_per_page = 25
    readonly_fields = [
        "uuid",
        "user",
        "item_count",
        "total_price",
        "shipping_address",
        "created_at",
        "updated_at",
    ]
    inlines = [OrderItemInline]
    actions = ["mark_as_shipping", "mark_as_completed", "cancel_orders"]
    fieldsets = (
        (None, {"fields": ("user", "status", "item_count")}),
        ("Payment", {"fields": ("total_price", "shipping_address")}),
        ("Timestamps", {"fields": ("uuid", "created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(items_total=Count("items", distinct=True))

    @admin.display(description="Order", ordering="pk")
    def order_number(self, obj):
        return f"#{obj.pk}"

    @admin.display(description="Items", ordering="items_total")
    def item_count(self, obj):
        return getattr(obj, "items_total", obj.items.count())

    def _apply_status(self, request, queryset, target, label):
        changed = 0
        for order in queryset:
            try:
                update_order_status(order, target)
                changed += 1
            except ValidationError as error:
                detail = error.detail if isinstance(error.detail, dict) else error.detail
                self.message_user(
                    request,
                    f"Order #{order.pk}: {detail}",
                    level="warning",
                )
        self.message_user(request, f"{changed} order(s) {label}.")

    @admin.action(description="Move selected orders to shipping")
    def mark_as_shipping(self, request, queryset):
        self._apply_status(request, queryset, Order.Status.SHIPPING, "moved to shipping")

    @admin.action(description="Move selected orders to completed")
    def mark_as_completed(self, request, queryset):
        self._apply_status(request, queryset, Order.Status.COMPLETED, "marked as completed")

    @admin.action(description="Cancel selected orders (restores stock)")
    def cancel_orders(self, request, queryset):
        self._apply_status(request, queryset, Order.Status.CANCELLED, "cancelled and restocked")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ["product", "quantity", "line_total"]
    readonly_fields = ["line_total"]
    autocomplete_fields = ["product"]

    @admin.display(description="Line total")
    def line_total(self, obj):
        if not obj.pk:
            return "—"
        return (obj.product.price * obj.quantity).quantize(Decimal("0.01"))


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "item_count", "total_price", "updated_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["uuid", "created_at", "updated_at", "item_count", "total_price"]
    inlines = [CartItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            items_total=Count("items", distinct=True),
            cart_total=Sum(F("items__product__price") * F("items__quantity")),
        )

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items_total

    @admin.display(description="Total")
    def total_price(self, obj):
        return obj.cart_total or Decimal("0.00")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["cart", "product", "quantity", "created_at"]
    search_fields = ["cart__user__username", "product__name"]
    list_filter = ["created_at"]
