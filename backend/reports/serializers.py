from rest_framework import serializers


class ProductTotalsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    in_stock = serializers.IntegerField()
    sold_out = serializers.IntegerField()
    low_stock = serializers.IntegerField()
    units_in_stock = serializers.IntegerField()
    catalogue_value = serializers.DecimalField(max_digits=14, decimal_places=2)


class CategoryTotalsSerializer(serializers.Serializer):
    total = serializers.IntegerField()


class CustomerTotalsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    with_orders = serializers.IntegerField()
    new_this_month = serializers.IntegerField()


class OrderTotalsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    pending = serializers.IntegerField()
    shipping = serializers.IntegerField()
    completed = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class SalesTotalsSerializer(serializers.Serializer):
    units = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    average_order = serializers.DecimalField(max_digits=14, decimal_places=2)


class TopProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock = serializers.IntegerField()
    units_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class TopCustomerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    order_count = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=14, decimal_places=2)
    last_order_at = serializers.DateTimeField(allow_null=True)


class RecentOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    uuid = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    status = serializers.CharField()
    status_display = serializers.CharField()
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    item_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class LowStockSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    stock = serializers.IntegerField()


class SalesPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    orders = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class CategoryBreakdownSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    products = serializers.IntegerField()
    units_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class DashboardSerializer(serializers.Serializer):
    generated_at = serializers.DateTimeField()
    products = ProductTotalsSerializer()
    categories = CategoryTotalsSerializer()
    customers = CustomerTotalsSerializer()
    orders = OrderTotalsSerializer()
    sales = SalesTotalsSerializer()
    top_products = TopProductSerializer(many=True)
    top_customers = TopCustomerSerializer(many=True)
    recent_orders = RecentOrderSerializer(many=True)
    low_stock = LowStockSerializer(many=True)
    sales_by_day = SalesPointSerializer(many=True)
    category_breakdown = CategoryBreakdownSerializer(many=True)


class ProductSaleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    image = serializers.ImageField(source="image_name", required=False)
    category = serializers.CharField(source="category_name", allow_null=True)
    category_id = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock = serializers.IntegerField()
    units_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    order_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class CustomerReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    role = serializers.CharField()
    is_active = serializers.BooleanField()
    date_joined = serializers.DateTimeField()
    order_count = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    shipping_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=14, decimal_places=2)
    last_order_at = serializers.DateTimeField(allow_null=True)


class CustomerProfileSerializer(CustomerReportSerializer):
    phone_number = serializers.CharField(allow_null=True)
    age = serializers.IntegerField(allow_null=True)
    is_staff = serializers.BooleanField()
    last_login = serializers.DateTimeField(allow_null=True)
    full_name = serializers.CharField(source="get_full_name", read_only=True)


class CustomerOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    uuid = serializers.UUIDField()
    status = serializers.CharField()
    status_display = serializers.CharField(source="get_status_display")
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    item_count = serializers.IntegerField(source="items.count")
    shipping_address = serializers.CharField()
    created_at = serializers.DateTimeField()
