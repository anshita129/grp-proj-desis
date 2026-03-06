from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts_app.permissions.role_permissions import IsLandlord
from props_app.models import ComplianceItem, Property
from props_app.serializers.compliance_serializers import ComplianceItemSerializer
from props_app.services.audit_log_service import log_domain_audit
from props_app.services.notification_service import compliance_status_for_date


def refresh_compliance_status(item: ComplianceItem):
    new_status = compliance_status_for_date(
        due_date=item.due_date,
        reminder_days_before=item.reminder_days_before,
    )
    if item.status != new_status:
        item.status = new_status
        item.save(update_fields=["status"])


class PropertyComplianceListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsLandlord]
    serializer_class = ComplianceItemSerializer

    def get_queryset(self):
        property_id = self.kwargs["property_id"]
        qs = ComplianceItem.objects.filter(
            property_id=property_id,
            property__owner=self.request.user,
        ).select_related("unit")
        only_overdue = self.request.query_params.get("only_overdue")
        unit_id = self.request.query_params.get("unit_id")
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        for item in qs:
            refresh_compliance_status(item)
        if str(only_overdue).lower() in {"1", "true", "yes"}:
            qs = qs.filter(status="OVERDUE")
        return qs.order_by("due_date")

    def perform_create(self, serializer):
        property_obj = get_object_or_404(
            Property,
            id=self.kwargs["property_id"],
            owner=self.request.user,
        )
        unit_obj = serializer.validated_data.get("unit")
        if unit_obj is None:
            raise ValidationError({"unit": "This field is required."})
        if unit_obj.property_id != property_obj.id:
            raise ValidationError(
                {"unit": "Selected unit does not belong to this property."}
            )
        item = serializer.save(property=property_obj)
        refresh_compliance_status(item)
        log_domain_audit(
            request=self.request,
            actor_user=self.request.user,
            entity_type="ComplianceItem",
            entity_id=item.id,
            action="compliance_item_created",
            after_json=ComplianceItemSerializer(item).data,
        )


class ComplianceItemUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsLandlord]
    serializer_class = ComplianceItemSerializer
    lookup_url_kwarg = "item_id"

    def get_queryset(self):
        return ComplianceItem.objects.filter(property__owner=self.request.user).select_related(
            "property",
            "unit",
        )

    def perform_update(self, serializer):
        before = ComplianceItemSerializer(self.get_object()).data
        item = serializer.save()
        refresh_compliance_status(item)
        log_domain_audit(
            request=self.request,
            actor_user=self.request.user,
            entity_type="ComplianceItem",
            entity_id=item.id,
            action="compliance_item_updated",
            before_json=before,
            after_json=ComplianceItemSerializer(item).data,
        )

    def perform_destroy(self, instance):
        before = ComplianceItemSerializer(instance).data
        item_id = instance.id
        instance.delete()
        log_domain_audit(
            request=self.request,
            actor_user=self.request.user,
            entity_type="ComplianceItem",
            entity_id=item_id,
            action="compliance_item_deleted",
            before_json=before,
            after_json={"deleted": True, "id": item_id},
        )


class ComplianceAlertsView(APIView):
    permission_classes = [IsLandlord]

    def get(self, request):
        qs = ComplianceItem.objects.filter(property__owner=request.user).select_related(
            "property",
            "unit",
        )
        for item in qs:
            refresh_compliance_status(item)

        property_id = request.query_params.get("property_id")
        if property_id:
            qs = qs.filter(property_id=property_id)
        unit_id = request.query_params.get("unit_id")
        if unit_id:
            qs = qs.filter(unit_id=unit_id)

        overdue = qs.filter(status="OVERDUE").count()
        due_soon = qs.filter(status="DUE_SOON").count()
        return Response(
            {
                "overdue_count": overdue,
                "due_soon_count": due_soon,
                "rows": ComplianceItemSerializer(qs.order_by("due_date"), many=True).data,
            }
        )