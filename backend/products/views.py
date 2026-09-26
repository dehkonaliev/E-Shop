from django.db import transaction
from django.db.models import Avg, Count, Exists, OuterRef, ProtectedError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated

from authentication.permissions import IsAdminRole
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import ProductFilter
from .models import Category, Like, Product
from .serializers import (
    CategorySerializer,
    LikeSerializer,
    ProductSerializer,
)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action in {"list", "retrieve", "metadata"}:
            return [AllowAny()]
        return [IsAdminRole()]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError(
                {"detail": "Delete related products and subcategories first."}
            ) from exc

    @extend_schema(tags=["Categories"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Categories"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Categories"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Categories"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Categories"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Categories"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "name", "stock"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Product.objects.select_related("category")
        user = self.request.user if self.request.user.is_authenticated else None
        like_filter = Like.objects.filter(product=OuterRef("pk"))
        if user is not None:
            like_filter = like_filter.filter(user=user)
        aggregates = {
            "likes_count": Count("likes", distinct=True),
            "average_rating": Avg("comments__rating"),
            "is_liked": Exists(like_filter),
        }
        return queryset.annotate(**aggregates)

    def get_permissions(self):
        if self.action in {"list", "retrieve", "metadata"}:
            return [AllowAny()]
        if self.action == "like":
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError(
                {"detail": "This product is used by a cart or order."}
            ) from exc

    @extend_schema(tags=["Products"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Products"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Products"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Products"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Products"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Products"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        tags=["Interactions"],
        request=None,
        responses={
            200: OpenApiResponse(description="Current like state and total count"),
        },
    )
    @action(detail=True, methods=["post"], url_path="like")
    def like(self, request, pk=None):
        with transaction.atomic():
            product = get_object_or_404(
                Product.objects.select_for_update(),
                pk=pk,
            )
            like, created = Like.objects.get_or_create(
                user=request.user,
                product=product,
            )
            if not created:
                like.delete()
        return Response(
            {
                "liked": created,
                "product_id": product.pk,
                "likes_count": product.likes.count(),
            }
        )


class LikeViewSet(ReadOnlyModelViewSet):
    queryset = Like.objects.none()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return Like.objects.filter(user=self.request.user).select_related("product")

    @extend_schema(tags=["Interactions"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Interactions"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
