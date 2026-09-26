from django.contrib import admin
from django.db.models import Avg, Count
from django.utils.html import format_html

from .models import Category, Like, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "parent",
        "children_count",
        "product_count",
        "created_at",
    ]
    list_filter = ["parent", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["uuid", "created_at", "updated_at"]
    ordering = ["name"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent")}),
        ("Details", {"fields": ("uuid", "created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            children_total=Count("children", distinct=True),
            products_total=Count("products", distinct=True),
        )

    @admin.display(description="Subcategories", ordering="children_total")
    def children_count(self, obj):
        return obj.children_total

    @admin.display(description="Products", ordering="products_total")
    def product_count(self, obj):
        return obj.products_total


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "thumbnail",
        "name",
        "category",
        "price",
        "stock",
        "availability",
        "likes_total",
        "rating_average",
        "created_at",
    ]
    list_filter = ["category", "created_at", "stock"]
    search_fields = ["name", "description", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["uuid", "created_at", "updated_at", "likes_total", "rating_average"]
    list_per_page = 25
    ordering = ["-created_at"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "description")}),
        ("Pricing and stock", {"fields": ("price", "stock", "image")}),
        ("Insights", {"fields": ("likes_total", "rating_average")}),
        ("Timestamps", {"fields": ("uuid", "created_at", "updated_at")}),
    )
    actions = ["mark_as_sold_out", "restock"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            likes_total=Count("likes", distinct=True),
        )

    @admin.display(description="Image")
    def thumbnail(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" alt="{}" style="width:46px;height:46px;'
            'object-fit:cover;border-radius:8px;border:1px solid #e8e8e8" />',
            obj.image.url,
            obj.name,
        )

    @admin.display(description="Availability", ordering="stock")
    def availability(self, obj):
        if obj.stock == 0:
            return "Sold out"
        if obj.stock <= 5:
            return f"Low ({obj.stock})"
        return "In stock"

    @admin.display(description="Likes", ordering="likes_total")
    def likes_total(self, obj):
        return getattr(obj, "likes_total", 0)

    @admin.display(description="Reviews")
    def rating_average(self, obj):
        average = obj.comments.aggregate(value=Avg("rating"))["value"]
        if average is None:
            return "No reviews"
        return f"{average:.1f} / 5"

    @admin.action(description="Set stock to zero (mark as sold out)")
    def mark_as_sold_out(self, request, queryset):
        updated = queryset.update(stock=0)
        self.message_user(request, f"{updated} product(s) marked as sold out.")

    @admin.action(description="Restock selected products to 25 units")
    def restock(self, request, queryset):
        updated = queryset.update(stock=25)
        self.message_user(request, f"{updated} product(s) restocked to 25 units.")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "user__email", "product__name"]
    autocomplete_fields = ["user", "product"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
