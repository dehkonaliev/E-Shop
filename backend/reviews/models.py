from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from baseapp.models import BaseModel


class Comment(BaseModel):
    user = models.ForeignKey(
        "authentication.CustomUser",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField(max_length=2000)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("user", "product")]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="comment_rating_between_1_and_5",
            )
        ]

    def __str__(self):
        return f"Comment by {self.user} on {self.product}"
