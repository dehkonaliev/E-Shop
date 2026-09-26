from rest_framework import serializers

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "uuid",
            "user",
            "user_id",
            "product",
            "text",
            "rating",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "user",
            "user_id",
            "product",
            "created_at",
        ]

    def validate_text(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("Comment text cannot be empty.")
        return text

    def validate(self, attrs):
        request = self.context.get("request")
        product = self.context.get("product")
        if request is not None and product is not None and self.instance is None:
            already_reviewed = Comment.objects.filter(
                user=request.user,
                product=product,
            ).exists()
            if already_reviewed:
                raise serializers.ValidationError(
                    "You have already reviewed this product."
                )
        return attrs
