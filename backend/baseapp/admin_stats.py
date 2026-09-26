from decimal import Decimal

from django.db.models import Count, F, Q, Sum, Value
from django.db.models.functions import Coalesce

RECENT_ORDERS_LIMIT = 8
TOP_CUSTOMERS_LIMIT = 6
LOW_STOCK_LIMIT = 8
LOW_STOCK_THRESHOLD = 5


def _money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(value).quantize(Decimal("0.01"))


def collect_dashboard_stats() -> dict:
    from authentication.models import CustomUser
    from orders.models import Order
    from products.models import Category, Product
    from reviews.models import Comment

    product_stats = Product.objects.aggregate(
        total=Count("id"),
        in_stock=Count("id", filter=Q(stock__gt=0)),
        sold_out=Count("id", filter=Q(stock=0)),
        units=Coalesce(Sum("stock"), Value(0)),
        catalogue_value=Coalesce(
            Sum(F("stock") * F("price")),
            Value(Decimal("0.00")),
        ),
    )

    order_stats = Order.objects.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status=Order.Status.PENDING)),
        shipping=Count("id", filter=Q(status=Order.Status.SHIPPING)),
        completed=Count("id", filter=Q(status=Order.Status.COMPLETED)),
        cancelled=Count("id", filter=Q(status=Order.Status.CANCELLED)),
        revenue=Coalesce(
            Sum("total_price", filter=~Q(status=Order.Status.CANCELLED)),
            Value(Decimal("0.00")),
        ),
    )

    top_customers = (
        CustomUser.objects.annotate(
            order_count=Count("orders", distinct=True),
            items_ordered=Count("orders__items", distinct=True),
            total_spent=Coalesce(
                Sum(
                    "orders__total_price",
                    filter=~Q(orders__status=Order.Status.CANCELLED),
                ),
                Value(Decimal("0.00")),
            ),
        )
        .filter(order_count__gt=0)
        .order_by("-order_count", "-total_spent")
        .values(
            "id",
            "username",
            "email",
            "order_count",
            "items_ordered",
            "total_spent",
        )[:TOP_CUSTOMERS_LIMIT]
    )

    recent_orders = [
        {
            **row,
            "status_display": Order.Status(row["status"]).label,
        }
        for row in (
            Order.objects.select_related("user")
            .annotate(item_count=Count("items"))
            .order_by("-created_at")
            .values(
                "id",
                "uuid",
                "user__username",
                "user__email",
                "status",
                "total_price",
                "created_at",
                "item_count",
            )[:RECENT_ORDERS_LIMIT]
        )
    ]

    low_stock = (
        Product.objects.filter(stock__lte=LOW_STOCK_THRESHOLD)
        .select_related("category")
        .order_by("stock", "name")
        .values("id", "name", "slug", "stock", "category__name")[:LOW_STOCK_LIMIT]
    )

    return {
        "products": {
            "total": product_stats["total"],
            "in_stock": product_stats["in_stock"],
            "sold_out": product_stats["sold_out"],
            "units": product_stats["units"],
            "catalogue_value": _money(product_stats["catalogue_value"]),
        },
        "categories": Category.objects.count(),
        "comments": Comment.objects.count(),
        "customers": CustomUser.objects.filter(role=CustomUser.Role.CUSTOMER).count(),
        "staff": CustomUser.objects.filter(is_staff=True).count(),
        "orders": {
            "total": order_stats["total"],
            "pending": order_stats["pending"],
            "shipping": order_stats["shipping"],
            "completed": order_stats["completed"],
            "cancelled": order_stats["cancelled"],
            "revenue": _money(order_stats["revenue"]),
        },
        "top_customers": list(top_customers),
        "recent_orders": recent_orders,
        "low_stock": list(low_stock),
    }
