from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce

from .models import CustomUser, SingUpCode, TempToken, TempUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = [
        "username",
        "email",
        "phone_number",
        "role",
        "order_count",
        "total_spent",
        "comment_count",
        "is_active",
        "is_staff",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "date_joined"]
    search_fields = ["username", "email", "phone_number", "first_name", "last_name"]
    ordering = ["-date_joined"]
    list_per_page = 25
    fieldsets = UserAdmin.fieldsets + (
        ("Store information", {"fields": ("phone_number", "age", "role")}),
        (
            "Purchase history",
            {"fields": ("order_count", "total_spent", "comment_count")},
        ),
    )
    readonly_fields = ["order_count", "total_spent", "comment_count"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            orders_total=Count("orders", distinct=True),
            comments_total=Count("comments", distinct=True),
            spent_total=Coalesce(
                Sum(
                    "orders__total_price",
                    filter=~Q(orders__status="cancelled"),
                ),
                Value(Decimal("0.00")),
            ),
        )

    @admin.display(description="Orders", ordering="orders_total")
    def order_count(self, obj):
        return obj.orders_total

    @admin.display(description="Spent", ordering="spent_total")
    def total_spent(self, obj):
        return Decimal(obj.spent_total).quantize(Decimal("0.01"))

    @admin.display(description="Reviews", ordering="comments_total")
    def comment_count(self, obj):
        return obj.comments_total


@admin.register(TempUser)
class TempUserAdmin(admin.ModelAdmin):
    list_display = ["email", "created_at"]
    search_fields = ["email"]
    readonly_fields = ["uuid", "created_at", "updated_at"]


@admin.register(SingUpCode)
class SingUpCodeAdmin(admin.ModelAdmin):
    list_display = ["user", "is_used", "expire_time", "created_at"]
    list_filter = ["is_used", "created_at"]
    search_fields = ["user__email"]
    readonly_fields = ["uuid", "code", "user", "created_at", "updated_at"]


@admin.register(TempToken)
class TempTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "is_used", "expire_time", "created_at"]
    list_filter = ["is_used", "created_at"]
    search_fields = ["user__email"]
    readonly_fields = ["uuid", "token", "user", "created_at", "updated_at"]
