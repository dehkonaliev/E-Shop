from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser
from products.models import Category, Product

from .models import Cart, CartItem, Order


class CartAndOrderApiTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="StrongPass123!",
        )
        self.other_user = CustomUser.objects.create_user(
            username="other-buyer",
            email="other-buyer@example.com",
            password="StrongPass123!",
        )
        self.admin = CustomUser.objects.create_user(
            username="order-admin",
            email="order-admin@example.com",
            password="StrongPass123!",
            is_staff=True,
            is_superuser=True,
        )
        category = Category.objects.create(name="Accessories")
        self.product = Product.objects.create(
            category=category,
            name="Keyboard",
            description="Mechanical keyboard",
            price="80.00",
            stock=5,
        )
        self.client.force_authenticate(self.user)

    def test_add_get_and_remove_cart_item(self):
        response = self.client.post(
            reverse("cart-add"),
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_price"], "160.00")
        self.assertEqual(CartItem.objects.get().quantity, 2)

        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)

        response = self.client.post(
            reverse("cart-remove"),
            {"product_id": self.product.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"], [])

    def test_checkout_creates_order_clears_cart_and_decrements_stock(self):
        self.client.post(
            reverse("cart-add"),
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )
        response = self.client.post(
            reverse("checkout"),
            {"shipping_address": "Tashkent, Uzbekistan"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_price"], "160.00")
        self.assertEqual(response.data["items"][0]["price_at_that_time"], "80.00")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertEqual(Order.objects.count(), 1)

    def test_failed_checkout_rolls_back_all_changes(self):
        self.client.post(
            reverse("cart-add"),
            {"product_id": self.product.pk, "quantity": 5},
            format="json",
        )
        self.product.stock = 2
        self.product.save(update_fields=["stock"])
        response = self.client.post(
            reverse("checkout"),
            {"shipping_address": "Tashkent, Uzbekistan"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(CartItem.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)

    def test_order_history_is_owner_scoped_and_status_is_admin_only(self):
        cart = Cart.objects.create(user=self.user)
        order = Order.objects.create(
            user=self.user,
            total_price=Decimal("80.00"),
            shipping_address="Tashkent",
        )
        order.items.create(
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            price_at_that_time=self.product.price,
        )
        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        self.client.force_authenticate(self.other_user)
        response = self.client.get(reverse("order-detail", args=[order.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("order-detail", args=[order.pk]),
            {"status": Order.Status.SHIPPING},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            reverse("order-detail", args=[order.pk]),
            {"status": Order.Status.SHIPPING},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Order.Status.SHIPPING)

    def test_cancelling_order_restores_stock_once(self):
        self.client.post(
            reverse("cart-add"),
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )
        self.client.post(
            reverse("checkout"),
            {"shipping_address": "Tashkent"},
            format="json",
        )
        order = Order.objects.get()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            reverse("order-detail", args=[order.pk]),
            {"status": Order.Status.CANCELLED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        second_response = self.client.patch(
            reverse("order-detail", args=[order.pk]),
            {"status": Order.Status.CANCELLED},
            format="json",
        )
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_invalid_status_transition_is_rejected(self):
        order = Order.objects.create(
            user=self.user,
            total_price=Decimal("80.00"),
            shipping_address="Tashkent",
        )
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            reverse("order-detail", args=[order.pk]),
            {"status": Order.Status.COMPLETED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_admin_can_list_customer_orders(self):
        Order.objects.create(
            user=self.user,
            total_price=Decimal("80.00"),
            shipping_address="Tashkent",
        )
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
