from django.urls import include, path

from baseapp.routers import PublicRootRouter

from .views import CommentViewSet

router = PublicRootRouter()
router.register(
    "products/(?P<product_pk>[0-9]+)/comments",
    CommentViewSet,
    basename="product-comments",
)

urlpatterns = [path("", include(router.urls))]
