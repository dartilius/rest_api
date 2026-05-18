from rest_framework import serializers

from feedback.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    # Фронт шлёт camelCase — маппим в snake_case модели
    brandId = serializers.CharField(source="brand_id", required=False, allow_null=True, allow_blank=True)
    nomenclaturesIds = serializers.ListField(
        child=serializers.CharField(),
        source="nomenclatures_ids",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Feedback
        fields = [
            "id",
            "code1c",
            "name",
            "phone",
            "email",
            "message",
            "pathname",
            "brandId",
            "nomenclaturesIds",
            "created",
        ]
        read_only_fields = ["id", "created"]