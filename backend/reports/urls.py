from django.urls import path

from .views import (
    CustomerDetailAPIView,
    CustomerOrdersAPIView,
    CustomerReportAPIView,
    DashboardAPIView,
    ProductSalesAPIView,
)

urlpatterns = [
    path("reports/dashboard/", DashboardAPIView.as_view(), name="report-dashboard"),
    path("reports/sales/", ProductSalesAPIView.as_view(), name="report-sales"),
    path("reports/customers/", CustomerReportAPIView.as_view(), name="report-customers"),
    path(
        "reports/customers/<int:pk>/",
        CustomerDetailAPIView.as_view(),
        name="report-customer-detail",
    ),
    path(
        "reports/customers/<int:pk>/orders/",
        CustomerOrdersAPIView.as_view(),
        name="report-customer-orders",
    ),
]
