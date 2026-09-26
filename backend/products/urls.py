from baseapp.routers import PublicRootRouter

from .views import CategoryViewSet, LikeViewSet, ProductViewSet

router = PublicRootRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("likes", LikeViewSet, basename="like")

urlpatterns = router.urls
