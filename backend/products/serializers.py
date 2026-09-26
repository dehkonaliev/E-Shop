from decimal import Decimal

from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from .models import Category, Like, Product


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "uuid",
            "name",
            "slug",
            "parent",
            "parent_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]

    def validate_slug(self, value):
        queryset = Category.objects.filter(slug=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("This slug is already in use.")
        return value

    def validate_parent(self, value):
        if value is None or self.instance is None:
            return value
        current = value
        visited = set()
        while current is not None and current.pk not in visited:
            if current.pk == self.instance.pk:
                raise serializers.ValidationError(
                    "A category cannot be a child of its own subcategory."
                )
            visited.add(current.pk)
            current = current.parent
        return value


class ProductSummarySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "uuid",
            "name",
            "slug",
            "price",
            "stock",
            "image",
        ]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        read_only=True,
    )
    is_liked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "uuid",
            "category",
            "category_name",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "image",
            "likes_count",
            "average_rating",
            "is_liked",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "likes_count",
            "average_rating",
            "is_liked",
            "created_at",
            "updated_at",
        ]

    def validate_price(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value

    def validate_image(self, image):
        if image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image size cannot exceed 5 MB.")
        try:
            with Image.open(image) as opened_image:
                opened_image.verify()
            image.seek(0)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise serializers.ValidationError("Upload a valid image file.") from exc
        return image


class LikeSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)

    class Meta:
        model = Like
        fields = ["id", "uuid", "product", "created_at"]
        read_only_fields = fields
