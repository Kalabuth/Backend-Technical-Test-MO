# apps/payments/views/payments_view.py

from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from apps.common.methods.custom_pagination import CustomPagination

from apps.authentication.mixins.api_key_protected_view_mixin import (
    ApiKeyProtectedViewMixin,
)
from apps.payments.models.payment import Payment
from apps.payments.serializers.payments_serializer import (
    PaymentCreateSerializer,
    PaymentReadSerializer,
)


class PaymentViewSet(ApiKeyProtectedViewMixin, viewsets.GenericViewSet):
    """
    list:
      GET /api/payments/?customer_external_id={external_id}
      Returns all payments, optionally filtered by customer.

    create:
      POST /api/payments/
      Creates a new payment and applies it across loans.

    retrieve:
      GET /api/payments/{external_id}/
      Returns a single payment by its external_id.
    """

    queryset = Payment.objects.all()
    lookup_field = "external_id"
    parser_classes = [JSONParser]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        return PaymentReadSerializer

    @swagger_auto_schema(
        operation_summary="List Payments",
        operation_description=(
            "Optionally filter by passing `?customer_external_id=<id>`; "
            "returns a list of payments matching that customer."
        ),
        manual_parameters=[
            openapi.Parameter(
                name="customer_external_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="External ID of the Customer to filter payments by",
                required=False,
            )
        ],
        responses={200: PaymentReadSerializer(many=True), 403: "Forbidden"},
    )
    def list(self, request):
        customer_id = request.query_params.get("customer_external_id")
        qs = self.get_queryset()
        if customer_id:
            qs = qs.filter(customer__external_id=customer_id)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Create Payment",
        operation_description=(
            "Creates a payment. "
            "Validates that the sum of parts equals `total_amount`, "
            "that it does not exceed total debt, and then applies it across loans."
        ),
        request_body=PaymentCreateSerializer,
        responses={201: PaymentReadSerializer, 400: "Bad Request", 403: "Forbidden"},
    )
    @transaction.atomic
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        output = PaymentReadSerializer(payment)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Retrieve Payment",
        operation_description="Fetch a single payment by its external_id.",
        responses={200: PaymentReadSerializer, 404: "Not Found", 403: "Forbidden"},
    )
    def retrieve(self, request, external_id=None):
        payment = self.get_object()
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
