from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, F, Max, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import CustomUser
from authentication.permissions import IsAdminRole
from baseapp.pagination import StandardPagination
from orders.models import Order, OrderItem
from products.models import Category, Product

from .serializers import (
    CustomerOrderSerializer,
    CustomerProfileSerializer,
    CustomerReportSerializer,
    DashboardSerializer,
    ProductSaleSerializer,
)

ZERO = Decimal("0.00")
LOW_STOCK_THRESHOLD = 5
CHART_DAYS = 14
RECENT_ORDERS_LIMIT = 8
TOP_LIMIT = 6


def money(value):
    return Decimal(value or 0).quantize(Decimal("0.01"))


def product_sale_annotations(prefix="order_items"):
    return {
        "units_sold": Coalesce(
            Sum(
                f"{prefix}__quantity",
                filter=~Q(
                    **{
                        f"{prefix}__order__status": Order.Status.CANCELLED,
                    }
                ),
            ),
            Value(0),
        ),
        "revenue": Coalesce(
            Sum(
                F(f"{prefix}__quantity") * F(f"{prefix}__price_at_that_time"),
                filter=~Q(
                    **{
                        f"{prefix}__order__status": Order.Status.CANCELLED,
                    }
                ),
            ),
            Value(ZERO),
        ),
        "order_count": Count(
            f"{prefix}__order",
            distinct=True,
            filter=~Q(
                **{
                    f"{prefix}__order__status": Order.Status.CANCELLED,
                }
            ),
        ),
    }


def product_sale_rows(queryset, limit=None):
    rows = queryset.values(
        "id",
        "name",
        "category__name",
        "price",
        "stock",
        "units_sold",
        "revenue",
        "order_count",
    )
    if limit:
        rows = rows[:limit]
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "category": row["category__name"],
            "price": money(row["price"]),
            "stock": row["stock"],
            "units_sold": row["units_sold"] or 0,
            "revenue": money(row["revenue"]),
        }
        for row in rows
    ]


def category_breakdown():
    rows = (
        Category.objects.annotate(
            products_total=Count("products", distinct=True),
            units_sold=Coalesce(
                Sum(
                    "products__order_items__quantity",
                    filter=~Q(
                        products__order_items__order__status=Order.Status.CANCELLED
                    ),
                ),
                Value(0),
            ),
            revenue=Coalesce(
                Sum(
                    F("products__order_items__quantity")
                    * F("products__order_items__price_at_that_time"),
                    filter=~Q(
                        products__order_items__order__status=Order.Status.CANCELLED
                    ),
                ),
                Value(ZERO),
            ),
        )
        .values("id", "name", "products_total", "units_sold", "revenue")
        .order_by("-revenue")[:TOP_LIMIT]
    )
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "products": row["products_total"],
            "units_sold": row["units_sold"] or 0,
            "revenue": money(row["revenue"]),
        }
        for row in rows
    ]


def customer_totals():
    return CustomUser.objects.filter(
        role=CustomUser.Role.CUSTOMER,
        is_staff=False,
    ).annotate(
        order_count=Count("orders", distinct=True),
        total_spent=Coalesce(
            Sum("orders__total_price", filter=~Q(orders__status=Order.Status.CANCELLED)),
            Value(ZERO),
        ),
        last_order_at=Max("orders__created_at"),
    )


def top_customers():
    rows = (
        customer_totals()
        .filter(order_count__gt=0)
        .order_by("-order_count", "-total_spent")[:TOP_LIMIT]
        .values("id", "username", "email", "order_count", "total_spent", "last_order_at")
    )
    return [
        {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"] or "",
            "order_count": row["order_count"],
            "total_spent": money(row["total_spent"]),
            "last_order_at": row["last_order_at"],
        }
        for row in rows
    ]


def recent_orders():
    rows = (
        Order.objects.select_related("user")
        .annotate(item_count=Count("items"))
        .order_by("-created_at")[:RECENT_ORDERS_LIMIT]
        .values(
            "id",
            "uuid",
            "user__username",
            "user__email",
            "status",
            "total_price",
            "item_count",
            "created_at",
        )
    )
    return [
        {
            "id": row["id"],
            "uuid": str(row["uuid"]),
            "username": row["user__username"],
            "email": row["user__email"] or "",
            "status": row["status"],
            "status_display": Order.Status(row["status"]).label,
            "total_price": money(row["total_price"]),
            "item_count": row["item_count"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def low_stock_products():
    rows = (
        Product.objects.select_related("category")
        .filter(stock__lte=LOW_STOCK_THRESHOLD)
        .order_by("stock", "name")[:RECENT_ORDERS_LIMIT]
        .values("id", "name", "category__name", "stock")
    )
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "category": row["category__name"],
            "stock": row["stock"],
        }
        for row in rows
    ]


def sales_by_day(days=CHART_DAYS):
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    rows = (
        Order.objects.filter(created_at__date__gte=start)
        .exclude(status=Order.Status.CANCELLED)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(orders=Count("id"), revenue=Sum("total_price"))
        .order_by("day")
    )
    lookup = {row["day"]: row for row in rows}
    points = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = lookup.get(day)
        points.append(
            {
                "date": day,
                "orders": row["orders"] if row else 0,
                "revenue": money(row["revenue"]) if row else ZERO,
            }
        )
    return points


class DashboardAPIView(APIView):
    permission_classes = [IsAdminRole]

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(
        tags=["Reports"],
        summary="Store dashboard statistics",
        responses={200: DashboardSerializer},
    )
    def get(self, request):
        product_totals = Product.objects.aggregate(
            total=Count("id"),
            in_stock=Count("id", filter=Q(stock__gt=0)),
            sold_out=Count("id", filter=Q(stock=0)),
            low_stock=Count("id", filter=Q(stock__lte=LOW_STOCK_THRESHOLD)),
            units_in_stock=Coalesce(Sum("stock"), Value(0)),
            catalogue_value=Coalesce(Sum(F("stock") * F("price")), Value(ZERO)),
        )
        order_totals = Order.objects.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status=Order.Status.PENDING)),
            shipping=Count("id", filter=Q(status=Order.Status.SHIPPING)),
            completed=Count("id", filter=Q(status=Order.Status.COMPLETED)),
            cancelled=Count("id", filter=Q(status=Order.Status.CANCELLED)),
            revenue=Coalesce(
                Sum("total_price", filter=~Q(status=Order.Status.CANCELLED)),
                Value(ZERO),
            ),
        )
        customer_totals_row = CustomUser.objects.filter(
            role=CustomUser.Role.CUSTOMER,
            is_staff=False,
        ).aggregate(
            total=Count("id"),
            with_orders=Count("id", filter=Q(orders__isnull=False), distinct=True),
            new_this_month=Count(
                "id",
                filter=Q(date_joined__date__gte=timezone.now().date().replace(day=1)),
            ),
        )
        sales_totals = OrderItem.objects.filter(
            order__status__in=[
                Order.Status.PENDING,
                Order.Status.SHIPPING,
                Order.Status.COMPLETED,
            ]
        ).aggregate(
            units=Coalesce(Sum("quantity"), Value(0)),
            revenue=Coalesce(
                Sum(F("quantity") * F("price_at_that_time")),
                Value(ZERO),
            ),
        )
        average_order = ZERO
        if order_totals["total"] > order_totals["cancelled"]:
            average_order = money(
                order_totals["revenue"] / (order_totals["total"] - order_totals["cancelled"])
            )
        top_products = product_sale_rows(
            Product.objects.annotate(**product_sale_annotations())
            .filter(units_sold__gt=0)
            .order_by("-units_sold", "-revenue"),
            limit=TOP_LIMIT,
        )
        payload = {
            "generated_at": timezone.now(),
            "products": {
                "total": product_totals["total"],
                "in_stock": product_totals["in_stock"],
                "sold_out": product_totals["sold_out"],
                "low_stock": product_totals["low_stock"],
                "units_in_stock": product_totals["units_in_stock"] or 0,
                "catalogue_value": money(product_totals["catalogue_value"]),
            },
            "categories": {"total": Category.objects.count()},
            "customers": {
                "total": customer_totals_row["total"],
                "with_orders": customer_totals_row["with_orders"],
                "new_this_month": customer_totals_row["new_this_month"],
            },
            "orders": {
                "total": order_totals["total"],
                "pending": order_totals["pending"],
                "shipping": order_totals["shipping"],
                "completed": order_totals["completed"],
                "cancelled": order_totals["cancelled"],
                "revenue": money(order_totals["revenue"]),
            },
            "sales": {
                "units": sales_totals["units"] or 0,
                "revenue": money(sales_totals["revenue"]),
                "average_order": average_order,
            },
            "top_products": top_products,
            "top_customers": top_customers(),
            "recent_orders": recent_orders(),
            "low_stock": low_stock_products(),
            "sales_by_day": sales_by_day(),
            "category_breakdown": category_breakdown(),
        }
        return Response(DashboardSerializer(payload).data)


class ProductSalesAPIView(APIView):
    permission_classes = [IsAdminRole]
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(
        tags=["Reports"],
        summary="Per product sales report",
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                description="Product name",
            ),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description=(
                    "units_sold, revenue, price, stock, name, created_at (prefix - for desc)"
                ),
            ),
        ],
        responses={200: ProductSaleSerializer(many=True)},
    )
    def get(self, request):
        queryset = (
            Product.objects.select_related("category")
            .annotate(
                category_name=F("category__name"),
                image_name=F("image"),
                **product_sale_annotations(),
            )
        )
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(name__icontains=search)
        allowed = {
            "units_sold": "units_sold",
            "revenue": "revenue",
            "price": "price",
            "stock": "stock",
            "name": "name",
            "created_at": "created_at",
        }
        ordering = request.query_params.get("ordering", "-units_sold")
        order_field = allowed.get(ordering.lstrip("-"), "-units_sold")
        prefix = "-" if ordering.startswith("-") else ""
        queryset = queryset.order_by(f"{prefix}{order_field}", "name")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ProductSaleSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class CustomerReportAPIView(APIView):
    permission_classes = [IsAdminRole]
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(
        tags=["Reports"],
        summary="Customers with order statistics",
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                description="Username, email or name",
            ),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description="order_count, spent, date_joined, username",
            ),
        ],
        responses={200: CustomerReportSerializer(many=True)},
    )
    def get(self, request):
        queryset = CustomUser.objects.annotate(**customer_order_annotations())
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        role = request.query_params.get("role")
        if role in CustomUser.Role.values:
            queryset = queryset.filter(role=role)
        else:
            queryset = queryset.filter(role=CustomUser.Role.CUSTOMER)
        queryset = queryset.filter(is_staff=False)
        if request.query_params.get("has_orders") in {"1", "true", "True"}:
            queryset = queryset.filter(order_count__gt=0)
        allowed = {
            "order_count": "order_count",
            "spent": "total_spent",
            "date_joined": "date_joined",
            "username": "username",
        }
        ordering = request.query_params.get("ordering", "-order_count")
        order_field = allowed.get(ordering.lstrip("-"), "-order_count")
        prefix = "-" if ordering.startswith("-") else ""
        queryset = queryset.order_by(f"{prefix}{order_field}", "username")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CustomerReportSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


def customer_order_annotations():
    return dict(
        order_count=Count("orders", distinct=True),
        pending_orders=Count(
            "orders",
            filter=Q(orders__status=Order.Status.PENDING),
            distinct=True,
        ),
        shipping_orders=Count(
            "orders",
            filter=Q(orders__status=Order.Status.SHIPPING),
            distinct=True,
        ),
        completed_orders=Count(
            "orders",
            filter=Q(orders__status=Order.Status.COMPLETED),
            distinct=True,
        ),
        cancelled_orders=Count(
            "orders",
            filter=Q(orders__status=Order.Status.CANCELLED),
            distinct=True,
        ),
        total_spent=Coalesce(
            Sum("orders__total_price", filter=~Q(orders__status=Order.Status.CANCELLED)),
            Value(ZERO),
        ),
        last_order_at=Max("orders__created_at"),
    )


class CustomerDetailAPIView(APIView):
    permission_classes = [IsAdminRole]

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(
        tags=["Reports"],
        summary="Customer profile with order statistics",
        responses={200: CustomerProfileSerializer},
    )
    def get(self, request, pk):
        customer = (
            CustomUser.objects.filter(pk=pk, is_staff=False)
            .annotate(**customer_order_annotations())
            .first()
        )
        if customer is None:
            return Response(
                {"detail": "Customer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CustomerProfileSerializer(customer).data)


class CustomerOrdersAPIView(APIView):
    permission_classes = [IsAdminRole]
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(
        tags=["Reports"],
        summary="Orders placed by one customer",
        responses={200: CustomerOrderSerializer(many=True)},
    )
    def get(self, request, pk):
        if not CustomUser.objects.filter(pk=pk, is_staff=False).exists():
            return Response(
                {"detail": "Customer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        queryset = Order.objects.filter(user_id=pk).order_by("-created_at")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CustomerOrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
