from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["product__name", "user__username", "text"]
    autocomplete_fields = ["product", "user"]
    readonly_fields = ["uuid", "user", "created_at", "updated_at"]
    list_per_page = 25
    fieldsets = (
        (None, {"fields": ("product", "user", "rating", "text")}),
        ("Timestamps", {"fields": ("uuid", "created_at", "updated_at")}),
    )
