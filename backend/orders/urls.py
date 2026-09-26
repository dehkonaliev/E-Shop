from django.urls import include, path

from baseapp.routers import PublicRootRouter

from .views import (
    CartAddAPIView,
    CartAPIView,
    CartRemoveAPIView,
    CheckoutAPIView,
    OrderViewSet,
)

router = PublicRootRouter()
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("cart/", CartAPIView.as_view(), name="cart"),
    path("cart/add/", CartAddAPIView.as_view(), name="cart-add"),
    path("cart/remove/", CartRemoveAPIView.as_view(), name="cart-remove"),
    path("orders/checkout/", CheckoutAPIView.as_view(), name="checkout"),
    path("", include(router.urls)),
]
