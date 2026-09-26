from django.contrib import admin

from .admin_stats import collect_dashboard_stats


class EshopAdminSite(admin.AdminSite):
    site_header = "E-Shop administration"
    site_title = "E-Shop admin"
    index_title = "Store dashboard"

    def index(self, request, extra_context=None):
        context = dict(extra_context or {})
        context["eshop_stats"] = collect_dashboard_stats()
        return super().index(request, context)


admin.site.__class__ = EshopAdminSite
