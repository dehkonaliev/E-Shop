from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter


class PublicRootRouter(DefaultRouter):
    def get_api_root_view(self, api_urls=None):
        api_root_view = super().get_api_root_view()
        api_root_view.cls.permission_classes = [AllowAny]
        return api_root_view
