from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser
from products.models import Category, Product

from .models import Comment


class CommentApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Books")
        self.product = Product.objects.create(
            category=self.category,
            name="Django Guide",
            description="Build APIs with Django",
            price="35.00",
            stock=10,
        )
        self.user = CustomUser.objects.create_user(
            username="reviewer",
            email="reviewer@example.com",
            password="StrongPass123!",
        )

    def test_comments_are_public_but_creation_requires_authentication(self):
        url = reverse("product-comments-list", args=[self.product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            url,
            {"text": "Useful book", "rating": 5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.user)
        response = self.client.post(
            url,
            {"text": "Useful book", "rating": 5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_comment_rating_must_be_between_one_and_five(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("product-comments-list", args=[self.product.pk]),
            {"text": "Invalid rating", "rating": 6},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_product_returns_not_found_for_comments(self):
        response = self.client.get(
            reverse("product-comments-list", args=[999999])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_one_review_per_user_and_product_is_enforced(self):
        url = reverse("product-comments-list", args=[self.product.pk])
        self.client.force_authenticate(self.user)

        first = self.client.post(
            url,
            {"text": "Great book", "rating": 5},
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(
            url,
            {"text": "Changed my mind", "rating": 3},
            format="json",
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already reviewed", str(second.data).lower())
        self.assertEqual(Comment.objects.filter(product=self.product).count(), 1)

    def test_another_user_can_review_the_same_product(self):
        url = reverse("product-comments-list", args=[self.product.pk])
        other = CustomUser.objects.create_user(
            username="second-reviewer",
            email="second@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(self.user)
        self.client.post(url, {"text": "Helpful", "rating": 4}, format="json")

        self.client.force_authenticate(other)
        response = self.client.post(
            url,
            {"text": "Also helpful", "rating": 5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.filter(product=self.product).count(), 2)

    def test_duplicate_comment_rows_are_rejected_by_the_database(self):
        Comment.objects.create(
            user=self.user,
            product=self.product,
            text="First",
            rating=4,
        )
        with self.assertRaises(IntegrityError):
            Comment.objects.create(
                user=self.user,
                product=self.product,
                text="Second",
                rating=2,
            )
