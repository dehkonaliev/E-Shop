from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from authentication.models import CustomUser
from authentication.permissions import IsAdminRole

from .models import Cart, CartItem, Order
from .serializers import (
    CartAddSerializer,
    CartRemoveSerializer,
    CartSerializer,
    CheckoutSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)
from .services import (
    add_to_cart,
    checkout_cart,
    get_or_create_cart,
    remove_from_cart,
    update_order_status,
)


def get_cart(user):
    cart = get_or_create_cart(user)
    return Cart.objects.prefetch_related(
        Prefetch(
            "items",
            queryset=CartItem.objects.select_related("product").order_by("created_at"),
        )
    ).get(pk=cart.pk)


class OptionsAllowAnyMixin:
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]
        return super().get_permissions()


class CartAPIView(OptionsAllowAnyMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Cart"], responses={200: CartSerializer})
    def get(self, request):
        return Response(CartSerializer(get_cart(request.user)).data)


class CartAddAPIView(OptionsAllowAnyMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Cart"],
        request=CartAddSerializer,
        responses={200: CartSerializer},
    )
    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        add_to_cart(
            request.user,
            serializer.validated_data["product_id"],
            serializer.validated_data["quantity"],
        )
        return Response(CartSerializer(get_cart(request.user)).data)


class CartRemoveAPIView(OptionsAllowAnyMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Cart"],
        request=CartRemoveSerializer,
        responses={200: CartSerializer},
    )
    def post(self, request):
        serializer = CartRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remove_from_cart(
            request.user,
            serializer.validated_data["product_id"],
        )
        return Response(CartSerializer(get_cart(request.user)).data)


class CheckoutAPIView(OptionsAllowAnyMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Orders"],
        request=CheckoutSerializer,
        responses={201: OrderSerializer},
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = checkout_cart(
            request.user,
            serializer.validated_data["shipping_address"],
        )
        order = (
            Order.objects.select_related("user")
            .prefetch_related("items__product")
            .get(pk=order.pk)
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.none()
    serializer_class = OrderSerializer
    http_method_names = ["get", "post", "put", "patch", "head", "options"]
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "total_price", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        queryset = Order.objects.select_related("user").prefetch_related(
            "items__product"
        )
        if self.request.user.is_staff or self.request.user.role == CustomUser.Role.ADMIN:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]
        if self.action in {"update", "partial_update"}:
            return [IsAdminRole()]
        return [IsAuthenticated()]

    @extend_schema(tags=["Orders"], responses={200: OrderSerializer})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Orders"], responses={200: OrderSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        order = self.get_object()
        serializer = OrderStatusSerializer(
            order,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        order = update_order_status(order, serializer.validated_data["status"])
        order = (
            Order.objects.select_related("user")
            .prefetch_related("items__product")
            .get(pk=order.pk)
        )
        return Response(OrderSerializer(order).data)

    partial_update = update

    @extend_schema(
        tags=["Orders"],
        request=OrderStatusSerializer,
        responses={200: OrderSerializer, 400: OpenApiTypes.OBJECT},
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        tags=["Orders"],
        request=OrderStatusSerializer,
        responses={200: OrderSerializer, 400: OpenApiTypes.OBJECT},
    )
    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
