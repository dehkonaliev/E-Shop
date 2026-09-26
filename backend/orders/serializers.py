from decimal import Decimal

from rest_framework import serializers

from .models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    unit_price = serializers.DecimalField(
        source="product.price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "line_total",
        ]
        read_only_fields = fields

    def get_line_total(self, obj: CartItem) -> str:
        return str((obj.product.price * obj.quantity).quantize(Decimal("0.01")))


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "uuid", "items", "total_price", "created_at", "updated_at"]
        read_only_fields = fields

    def get_total_price(self, obj: Cart) -> str:
        total = sum(
            (
                item.product.price * item.quantity
                for item in obj.items.all()
            ),
            Decimal("0.00"),
        )
        return str(total.quantize(Decimal("0.01")))


class CartAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartRemoveSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(max_length=1000, trim_whitespace=True)

    def validate_shipping_address(self, value):
        if not value.strip():
            raise serializers.ValidationError("Shipping address cannot be empty.")
        return value.strip()


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "price_at_that_time",
            "line_total",
        ]
        read_only_fields = fields

    def get_line_total(self, obj: OrderItem) -> str:
        return str((obj.price_at_that_time * obj.quantity).quantize(Decimal("0.01")))


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "uuid",
            "user",
            "user_username",
            "user_email",
            "total_price",
            "status",
            "status_display",
            "shipping_address",
            "items",
            "item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)

    class Meta:
        model = Order
        fields = ["status"]
