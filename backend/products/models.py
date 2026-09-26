from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from baseapp.models import BaseModel


def product_image_path(instance, filename):
    return f"products/{instance.slug}/{filename}"


def generate_unique_slug(model, name, instance):
    base_slug = slugify(name) or "item"
    slug = base_slug
    suffix = 2
    while True:
        queryset = model.objects.filter(slug=slug)
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)
        if not queryset.exists():
            return slug
        slug = f"{base_slug}-{suffix}"
        suffix += 1


class Category(BaseModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def clean(self):
        if self.parent_id and self.parent_id == self.pk:
            raise ValueError("A category cannot be its own parent")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Category, self.name, self)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(BaseModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to=product_image_path, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "price"]),
            models.Index(fields=["-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="product_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name="product_stock_nonnegative",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Product, self.name, self)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Like(BaseModel):
    user = models.ForeignKey(
        "authentication.CustomUser",
        on_delete=models.CASCADE,
        related_name="likes",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_like",
            )
        ]

    def __str__(self):
        return f"{self.user} likes {self.product}"
