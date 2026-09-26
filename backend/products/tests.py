import base64

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser
from orders.models import Cart, CartItem, Order
from orders.services import checkout_cart

from .models import Category, Like, Product


class CatalogApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            category=self.category,
            name="Wireless Headphones",
            description="Noise cancelling headphones",
            price="120.00",
            stock=5,
        )
        self.customer = CustomUser.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="StrongPass123!",
        )
        self.admin = CustomUser.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="StrongPass123!",
            is_staff=True,
            is_superuser=True,
        )

    def test_catalog_is_public_and_supports_filter_search_and_ordering(self):
        response = self.client.get(
            reverse("product-list"),
            {
                "category": self.category.slug,
                "min_price": "100",
                "max_price": "150",
                "search": "Headphones",
                "ordering": "price",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.product.pk)

    def test_only_admin_can_create_product(self):
        payload = {
            "category": self.category.pk,
            "name": "Phone",
            "description": "Smart phone",
            "price": "500.00",
            "stock": 3,
        }
        response = self.client.post(reverse("product-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(self.customer)
        response = self.client.post(reverse("product-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("product-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_like_toggle_and_like_list(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post(
            reverse("product-like", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["liked"])
        self.assertEqual(Like.objects.count(), 1)

        response = self.client.get(reverse("like-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        response = self.client.post(
            reverse("product-like", args=[self.product.pk])
        )
        self.assertFalse(response.data["liked"])
        self.assertEqual(Like.objects.count(), 0)

    def test_anonymous_product_response_contains_is_liked(self):
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("is_liked", response.data["results"][0])
        self.assertFalse(response.data["results"][0]["is_liked"])

    def test_duplicate_names_receive_unique_slugs(self):
        self.client.force_authenticate(self.admin)
        first_response = self.client.post(
            reverse("product-list"),
            {
                "category": self.category.pk,
                "name": "Same name",
                "description": "First",
                "price": "10.00",
                "stock": 1,
            },
            format="json",
        )
        second_response = self.client.post(
            reverse("product-list"),
            {
                "category": self.category.pk,
                "name": "Same name",
                "description": "Second",
                "price": "12.00",
                "stock": 1,
            },
            format="json",
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(first_response.data["slug"], second_response.data["slug"])

    def test_delete_product_used_in_cart_returns_validation_error(self):
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.force_authenticate(self.admin)
        response = self.client.delete(
            reverse("product-detail", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())


class AdminDashboardTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            username="storeadmin",
            email="admin@example.com",
            password="StrongPass123!",
        )
        self.customer = CustomUser.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="StrongPass123!",
        )
        self.category = Category.objects.create(name="Home")
        self.product = Product.objects.create(
            category=self.category,
            name="Ceramic Mug",
            description="Hand thrown mug",
            price="24.00",
            stock=3,
        )
        self.client.force_login(self.admin)

    def test_dashboard_shows_store_statistics(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.context["eshop_stats"]
        self.assertEqual(stats["products"]["total"], 1)
        self.assertEqual(stats["products"]["in_stock"], 1)
        self.assertEqual(stats["products"]["units"], 3)
        self.assertEqual(stats["categories"], 1)
        self.assertEqual(stats["customers"], 1)
        self.assertEqual(stats["orders"]["total"], 0)
        self.assertEqual(len(stats["low_stock"]), 1)

    def test_product_changelist_and_add_form_render(self):
        for url_name in ["admin:products_product_changelist", "admin:products_product_add"]:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_create_and_edit_a_product(self):
        response = self.client.post(
            reverse("admin:products_product_add"),
            {
                "name": "Linen Throw",
                "slug": "linen-throw",
                "category": self.category.pk,
                "description": "Washed linen blanket",
                "price": "89.90",
                "stock": "12",
                "image": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        created = Product.objects.get(slug="linen-throw")
        self.assertEqual(created.stock, 12)
        response = self.client.post(
            reverse("admin:products_product_change", args=[created.pk]),
            {
                "name": "Linen Throw",
                "slug": "linen-throw",
                "category": self.category.pk,
                "description": "Washed linen blanket, larger",
                "price": "94.00",
                "stock": "8",
                "image": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        created.refresh_from_db()
        self.assertEqual(created.stock, 8)

    def test_customer_admin_tracks_order_totals(self):
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        checkout_cart(self.customer, "12 Rivet Street")
        response = self.client.get(reverse("admin:authentication_customuser_changelist"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = response.context["cl"].result_list.get(username="buyer")
        self.assertEqual(row.orders_total, 1)
        self.assertEqual(str(row.spent_total), "48")

    def test_order_admin_action_moves_order_to_shipping(self):
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        order = checkout_cart(self.customer, "12 Rivet Street")
        response = self.client.post(
            reverse("admin:orders_order_changelist"),
            {
                "action": "mark_as_shipping",
                "_selected_action": [str(order.pk)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPING)

    def test_category_delete_is_blocked_while_products_exist(self):
        response = self.client.post(
            reverse("admin:products_category_delete", args=[self.category.pk]),
            {"post": "yes"},
            follow=True,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())


class AdminApiCrudTests(APITestCase):
    def setUp(self):
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
        self.category = Category.objects.create(name="Home")
        self.product = Product.objects.create(
            category=self.category,
            name="Linen Vase",
            description="A soft vase",
            price="24.00",
            stock=5,
        )
        self.client.force_authenticate(user=self.admin)

    def test_customer_cannot_create_or_delete_a_product(self):
        self.client.force_authenticate(user=self.customer)
        create = self.client.post(
            reverse("product-list"),
            {
                "category": self.category.pk,
                "name": "Nope",
                "description": "No",
                "price": "10.00",
                "stock": "1",
            },
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_403_FORBIDDEN)
        delete = self.client.delete(reverse("product-detail", args=[self.category.pk]))
        self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_create_edit_and_delete_round_trip(self):
        create = self.client.post(
            reverse("product-list"),
            {
                "category": self.category.pk,
                "name": "Brass Kettle",
                "description": "Stovetop kettle",
                "price": "54.50",
                "stock": "7",
            },
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        product_id = create.data["id"]
        self.assertEqual(create.data["slug"], "brass-kettle")

        update = self.client.patch(
            reverse("product-detail", args=[product_id]),
            {"price": "59.00", "stock": "3", "description": "Updated copy"},
            format="json",
        )
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        self.assertEqual(update.data["price"], "59.00")
        self.assertEqual(update.data["stock"], 3)
        self.assertEqual(update.data["name"], "Brass Kettle")

        delete = self.client.delete(reverse("product-detail", args=[product_id]))
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=product_id).exists())

    def test_product_delete_is_blocked_when_used_by_an_order(self):
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        checkout_cart(self.customer, "12 Rivet Street")
        response = self.client.delete(reverse("product-detail", args=[self.product.pk]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_product_multipart_edit_updates_fields_and_image(self):
        image = SimpleUploadedFile(
            "vase.png",
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmM"
                "IQAAAABJRU5ErkJggg=="
            ),
            content_type="image/png",
        )
        created = self.client.post(
            reverse("product-list"),
            {
                "category": self.category.pk,
                "name": "Stone Bowl",
                "description": "Hand thrown",
                "price": "40.00",
                "stock": "6",
                "image": image,
            },
            format="multipart",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        product_id = created.data["id"]
        self.assertTrue(created.data["image"])

        edited = self.client.patch(
            reverse("product-detail", args=[product_id]),
            {
                "name": "Stone Bowl Large",
                "description": "Hand thrown, larger",
                "price": "46.50",
                "stock": "9",
            },
            format="multipart",
        )
        self.assertEqual(edited.status_code, status.HTTP_200_OK)
        self.assertEqual(edited.data["name"], "Stone Bowl Large")
        self.assertEqual(edited.data["price"], "46.50")
        self.assertEqual(edited.data["stock"], 9)
        self.assertTrue(Product.objects.get(pk=product_id).image)

    def test_product_multipart_edit_rejects_invalid_values(self):
        response = self.client.patch(
            reverse("product-detail", args=[self.product.pk]),
            {"price": "-5", "stock": "0"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(str(self.product.price), "24.00")

    def test_category_create_edit_and_delete_round_trip(self):
        create = self.client.post(
            reverse("category-list"),
            {"name": "Kitchen", "parent": None},
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        category_id = create.data["id"]
        self.assertEqual(create.data["slug"], "kitchen")

        child = self.client.post(
            reverse("category-list"),
            {"name": "Kettles", "parent": category_id},
            format="json",
        )
        self.assertEqual(child.status_code, status.HTTP_201_CREATED)

        update = self.client.patch(
            reverse("category-detail", args=[category_id]),
            {"name": "Kitchen & Dining"},
            format="json",
        )
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        self.assertEqual(update.data["name"], "Kitchen & Dining")

        blocked = self.client.delete(reverse("category-detail", args=[category_id]))
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.delete(reverse("category-detail", args=[child.data["id"]]))
        removed = self.client.delete(reverse("category-detail", args=[category_id]))
        self.assertEqual(removed.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=category_id).exists())
