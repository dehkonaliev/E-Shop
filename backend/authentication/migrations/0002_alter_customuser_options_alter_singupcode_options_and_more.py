from django.db import migrations, models
from django.utils.crypto import salted_hmac


def normalize_authentication_emails(apps, schema_editor):
    custom_user_model = apps.get_model("authentication", "CustomUser")
    temp_user_model = apps.get_model("authentication", "TempUser")
    temp_token_model = apps.get_model("authentication", "TempToken")
    seen_custom_emails = set()
    for user in custom_user_model.objects.order_by("pk"):
        email = (user.email or "").strip().lower() or None
        if email in seen_custom_emails:
            raise ValueError(
                f"Duplicate CustomUser email {email!r}; resolve it before migrating."
            )
        if email:
            seen_custom_emails.add(email)
        if user.email != email:
            user.email = email
            user.save(update_fields=["email"])
    seen_temp_emails = set()
    for temp_user in temp_user_model.objects.order_by("pk"):
        email = temp_user.email.strip().lower()
        if email in seen_temp_emails:
            raise ValueError(
                f"Duplicate TempUser email {email!r}; resolve it before migrating."
            )
        seen_temp_emails.add(email)
        if temp_user.email != email:
            temp_user.email = email
            temp_user.save(update_fields=["email"])
    for token in temp_token_model.objects.all():
        token.token = salted_hmac(
            "authentication.user-activation",
            token.token,
            secret="activation",
        ).hexdigest()
        token.save(update_fields=["token"])


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.RunPython(
            normalize_authentication_emails,
            migrations.RunPython.noop,
        ),
        migrations.AlterModelOptions(
            name='customuser',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='singupcode',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='temptoken',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='tempuser',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('admin', 'Admin'), ('customer', 'Customer')], default='customer', max_length=10),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='singupcode',
            name='code',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='temptoken',
            name='token',
            field=models.CharField(max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name='tempuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AddIndex(
            model_name='singupcode',
            index=models.Index(fields=['user', 'is_used', 'expire_time'], name='authenticat_user_id_8e4e14_idx'),
        ),
        migrations.AddIndex(
            model_name='temptoken',
            index=models.Index(fields=['user', 'is_used', 'expire_time'], name='authenticat_user_id_932f99_idx'),
        ),
    ]
