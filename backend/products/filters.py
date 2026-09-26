import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    category_id = django_filters.NumberFilter(field_name="category")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    in_stock = django_filters.ChoiceFilter(
        choices=(("true", "true"), ("false", "false")),
        method="filter_in_stock",
        label="In stock",
    )

    class Meta:
        model = Product
        fields = ["category", "category_id", "min_price", "max_price", "in_stock"]

    def filter_in_stock(self, queryset, _name, value):
        if value == "true":
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)
