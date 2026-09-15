from collections import Counter, defaultdict

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PlacementOrder
from .views import MarketingReportPermission


class MarketingReportQuerySerializer(serializers.Serializer):
    from_date = serializers.DateField(source="from")
    to = serializers.DateField()

    def to_internal_value(self, data):
        data = data.copy()
        if "from" in data:
            data["from_date"] = data["from"]
        return super().to_internal_value(data)

    def validate(self, attrs):
        if attrs["from"] > attrs["to"]:
            raise serializers.ValidationError({"to": "Must be on or after from."})
        return attrs


class PlacementOrderMarketingReportView(APIView):
    """Read-only aggregate funnel report with no client contact data."""

    permission_classes = [MarketingReportPermission]

    def get(self, request):
        query = MarketingReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        date_range = query.validated_data
        orders = PlacementOrder.objects.filter(
            created__date__range=(date_range["from"], date_range["to"])
        ).values("commercial_status", "attribution")

        by_status = Counter()
        by_source = defaultdict(lambda: {"created": 0, "booked": 0})
        by_landing_path = defaultdict(lambda: {"created": 0, "booked": 0})
        created = 0

        for order in orders.iterator():
            created += 1
            commercial_status = order["commercial_status"]
            by_status[commercial_status] += 1
            attribution = order["attribution"] or {}
            first_touch = attribution.get("first_touch") or {}

            source = first_touch.get("utm_source")
            medium = first_touch.get("utm_medium")
            source_label = f"{source or 'unattributed'} / {medium or 'unattributed'}"
            source_row = by_source[source_label]
            source_row["created"] += 1

            landing_path = first_touch.get("landing_path") or "unattributed"
            landing_row = by_landing_path[landing_path]
            landing_row["created"] += 1

            if commercial_status == "booked":
                source_row["booked"] += 1
                landing_row["booked"] += 1

        return Response({
            "created": created,
            "by_status": {
                key: by_status[key]
                for key in ("new", "qualified", "proposal_sent", "booked", "lost")
            },
            "by_source": [
                {
                    "source": source,
                    "created": metrics["created"],
                    "booked": metrics["booked"],
                    "booked_rate": round(metrics["booked"] / metrics["created"], 2),
                }
                for source, metrics in sorted(by_source.items())
            ],
            "by_landing_path": [
                {
                    "landing_path": landing_path,
                    "created": metrics["created"],
                    "booked": metrics["booked"],
                }
                for landing_path, metrics in sorted(by_landing_path.items())
            ],
        })
