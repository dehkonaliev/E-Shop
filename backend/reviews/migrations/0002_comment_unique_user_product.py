from django.db import migrations, models


def drop_duplicate_comments(apps, schema_editor):
    """Keep the newest comment per (user, product) pair before adding the constraint."""
    Comment = apps.get_model("reviews", "Comment")
    duplicates = (
        Comment.objects.values("user_id", "product_id")
        .annotate(total=models.Count("id"))
        .filter(total__gt=1)
    )
    for duplicate in duplicates:
        keep = (
            Comment.objects.filter(
                user_id=duplicate["user_id"],
                product_id=duplicate["product_id"],
            )
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
            .first()
        )
        Comment.objects.filter(
            user_id=duplicate["user_id"],
            product_id=duplicate["product_id"],
        ).exclude(id=keep).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("reviews", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(drop_duplicate_comments, noop),
        migrations.AlterUniqueTogether(
            name="comment",
            unique_together={("user", "product")},
        ),
    ]
