from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from products.models import Product

from .models import Comment
from .serializers import CommentSerializer


class CommentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    queryset = Comment.objects.none()
    serializer_class = CommentSerializer
    http_method_names = ["get", "post", "head", "options"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return Comment.objects.filter(
            product=self.get_product()
        ).select_related("user")

    def get_product(self):
        if getattr(self, "swagger_fake_view", False):
            return None
        return get_object_or_404(Product, pk=self.kwargs["product_pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        product = self.get_product()
        if product is not None:
            context["product"] = product
        return context

    def perform_create(self, serializer):
        product = get_object_or_404(Product, pk=self.kwargs["product_pk"])
        try:
            serializer.save(user=self.request.user, product=product)
        except IntegrityError as error:
            raise serializers.ValidationError(
                "You have already reviewed this product."
            ) from error

    @extend_schema(tags=["Interactions"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Interactions"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
