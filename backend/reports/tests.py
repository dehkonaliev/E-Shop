from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser
from orders.models import Cart, CartItem, Order, OrderItem
from orders.services import checkout_cart, get_or_create_cart, update_order_status
from products.models import Category, Product


class ReportTestMixin:
    def setUp(self):
        self.category = Category.objects.create(name="Home")
        self.product = Product.objects.create(
            category=self.category,
            name="Linen Vase",
            description="A soft vase.",
            price=Decimal("24.00"),
            stock=5,
        )
        self.seller = Product.objects.create(
            category=self.category,
            name="Clay Mug",
            description="A warm mug.",
            price=Decimal("12.00"),
            stock=1,
        )
        self.admin = CustomUser.objects.create_superuser(
            username="root",
            email="root@eshop.test",
            password="admin-password-123",
        )
        self.customer = CustomUser.objects.create_user(
            username="buyer",
            email="buyer@eshop.test",
            password="customer-password-123",
        )
        self.browser = CustomUser.objects.create_user(
            username="guest",
            email="guest@eshop.test",
            password="customer-password-123",
        )
        self.staff_customer = CustomUser.objects.create_user(
            username="staffer",
            email="staffer@eshop.test",
            password="customer-password-123",
            is_staff=True,
        )
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.order = checkout_cart(self.customer, "12 Rivet Street")

    def auth_admin(self):
        self.client.force_authenticate(user=self.admin)

    def auth_customer(self):
        self.client.force_authenticate(user=self.customer)


class DashboardTests(ReportTestMixin, APITestCase):
    def test_anonymous_user_cannot_read_dashboard(self):
        response = self.client.get(reverse("report-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_read_dashboard(self):
        self.auth_customer()
        response = self.client.get(reverse("report-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_reports_products_orders_and_sales(self):
        self.auth_admin()
        response = self.client.get(reverse("report-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["products"]["total"], 2)
        self.assertEqual(data["products"]["in_stock"], 2)
        self.assertEqual(data["products"]["units_in_stock"], 4)
        self.assertEqual(data["products"]["catalogue_value"], "84.00")
        self.assertEqual(data["categories"]["total"], 1)
        self.assertEqual(data["customers"]["total"], 2)
        self.assertEqual(data["customers"]["with_orders"], 1)
        self.assertEqual(data["orders"]["total"], 1)
        self.assertEqual(data["orders"]["pending"], 1)
        self.assertEqual(data["orders"]["revenue"], "48.00")
        self.assertEqual(data["sales"]["units"], 2)
        self.assertEqual(data["sales"]["revenue"], "48.00")
        self.assertEqual(len(data["sales_by_day"]), 14)
        self.assertEqual(data["sales_by_day"][-1]["revenue"], "48.00")

    def test_cancelled_orders_are_excluded_from_sales(self):
        update_order_status(self.order, Order.Status.SHIPPING)
        update_order_status(self.order, Order.Status.CANCELLED)
        self.auth_admin()
        data = self.client.get(reverse("report-dashboard")).data
        self.assertEqual(data["orders"]["cancelled"], 1)
        self.assertEqual(data["orders"]["revenue"], "0.00")
        self.assertEqual(data["sales"]["units"], 0)
        self.assertEqual(data["top_products"], [])

    def test_dashboard_lists_top_products_customers_and_low_stock(self):
        self.auth_admin()
        data = self.client.get(reverse("report-dashboard")).data
        self.assertEqual(data["top_products"][0]["name"], "Linen Vase")
        self.assertEqual(data["top_products"][0]["units_sold"], 2)
        self.assertEqual(data["top_products"][0]["revenue"], "48.00")
        self.assertEqual(data["top_customers"][0]["username"], "buyer")
        self.assertEqual(data["top_customers"][0]["total_spent"], "48.00")
        self.assertEqual(data["recent_orders"][0]["status"], "pending")
        self.assertEqual(data["low_stock"][0]["name"], "Clay Mug")
        self.assertEqual(data["category_breakdown"][0]["units_sold"], 2)


class ProductSalesTests(ReportTestMixin, APITestCase):
    def test_customer_cannot_read_sales_report(self):
        self.auth_customer()
        response = self.client.get(reverse("report-sales"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sales_report_is_paginated_and_sorted(self):
        self.auth_admin()
        response = self.client.get(reverse("report-sales"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["name"], "Linen Vase")
        self.assertEqual(response.data["results"][0]["units_sold"], 2)
        self.assertEqual(response.data["results"][0]["revenue"], "48.00")
        self.assertEqual(response.data["results"][0]["category"], "Home")
        self.assertEqual(response.data["results"][1]["units_sold"], 0)

    def test_sales_report_supports_search_and_ordering(self):
        self.auth_admin()
        response = self.client.get(
            reverse("report-sales"),
            {"search": "clay", "ordering": "-price"},
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Clay Mug")

    def test_sales_report_updates_after_new_order(self):
        cart = Cart.objects.create(user=self.browser)
        CartItem.objects.create(cart=cart, product=self.seller, quantity=1)
        checkout_cart(self.browser, "9 Kiln Way")
        self.auth_admin()
        response = self.client.get(reverse("report-sales"), {"search": "clay"})
        row = response.data["results"][0]
        self.assertEqual(row["units_sold"], 1)
        self.assertEqual(row["revenue"], "12.00")
        self.assertEqual(row["order_count"], 1)


class CustomerReportTests(ReportTestMixin, APITestCase):
    def test_anonymous_user_cannot_read_customers(self):
        response = self.client.get(reverse("report-customers"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_report_lists_customers_with_order_stats(self):
        self.auth_admin()
        response = self.client.get(reverse("report-customers"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        buyer = next(row for row in response.data["results"] if row["username"] == "buyer")
        self.assertEqual(buyer["order_count"], 1)
        self.assertEqual(buyer["pending_orders"], 1)
        self.assertEqual(buyer["completed_orders"], 0)
        self.assertEqual(buyer["total_spent"], "48.00")
        self.assertIsNotNone(buyer["last_order_at"])
        guest = next(row for row in response.data["results"] if row["username"] == "guest")
        self.assertEqual(guest["order_count"], 0)
        self.assertEqual(guest["total_spent"], "0.00")

    def test_report_excludes_admin_and_staff_accounts(self):
        self.auth_admin()
        response = self.client.get(reverse("report-customers"))
        usernames = {row["username"] for row in response.data["results"]}
        self.assertNotIn("root", usernames)
        self.assertNotIn("staffer", usernames)

    def test_report_supports_search_and_has_orders_filter(self):
        self.auth_admin()
        response = self.client.get(reverse("report-customers"), {"search": "buyer@"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["username"], "buyer")
        response = self.client.get(reverse("report-customers"), {"has_orders": "true"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["username"], "buyer")


class CustomerDetailTests(ReportTestMixin, APITestCase):
    def test_customer_cannot_read_other_customer_details(self):
        self.auth_customer()
        response = self.client.get(
            reverse("report-customer-detail", args=[self.browser.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_returns_profile_fields(self):
        self.customer.first_name = "Ari"
        self.customer.last_name = "Khan"
        self.customer.phone_number = "+998901234567"
        self.customer.age = 29
        self.customer.save()
        self.auth_admin()
        response = self.client.get(reverse("report-customer-detail", args=[self.customer.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["username"], "buyer")
        self.assertEqual(data["email"], "buyer@eshop.test")
        self.assertEqual(data["full_name"], "Ari Khan")
        self.assertEqual(data["phone_number"], "+998901234567")
        self.assertEqual(data["age"], 29)
        self.assertTrue(data["is_active"])
        self.assertFalse(data["is_staff"])
        self.assertEqual(data["order_count"], 1)
        self.assertEqual(data["total_spent"], "48.00")
        self.assertIsNotNone(data["last_order_at"])

    def test_detail_of_unknown_or_staff_account_is_404(self):
        self.auth_admin()
        missing = self.client.get(reverse("report-customer-detail", args=[9999]))
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)
        staff = self.client.get(reverse("report-customer-detail", args=[self.admin.id]))
        self.assertEqual(staff.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_orders_are_paginated_newest_first(self):
        cart = get_or_create_cart(self.customer)
        CartItem.objects.create(cart=cart, product=self.seller, quantity=1)
        second = checkout_cart(self.customer, "5 Kiln Way")
        self.auth_admin()
        response = self.client.get(
            reverse("report-customer-orders", args=[self.customer.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["id"], second.id)
        self.assertEqual(response.data["results"][0]["status"], "pending")
        self.assertEqual(response.data["results"][0]["item_count"], 1)
        self.assertEqual(response.data["results"][0]["total_price"], "12.00")
        self.assertEqual(
            response.data["results"][0]["shipping_address"],
            "5 Kiln Way",
        )

    def test_customer_orders_for_unknown_account_is_404(self):
        self.auth_admin()
        response = self.client.get(reverse("report-customer-orders", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ReportItemSnapshotTests(ReportTestMixin, APITestCase):
    def test_sales_use_price_at_purchase_time(self):
        self.product.price = Decimal("99.00")
        self.product.save(update_fields=["price", "updated_at"])
        item = OrderItem.objects.get(order=self.order)
        self.auth_admin()
        response = self.client.get(reverse("report-sales"), {"search": "linen"})
        self.assertEqual(response.data["results"][0]["revenue"], "48.00")
        self.assertEqual(item.price_at_that_time, Decimal("24.00"))
