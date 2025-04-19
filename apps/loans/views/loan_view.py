# apps/loans/views/loan_view.py

from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from apps.authentication.mixins.api_key_protected_view_mixin import (
    ApiKeyProtectedViewMixin,
)
from apps.loans.models.loans import Loan, LoanStatus
from apps.loans.serializers.loan_serializer import LoanCreateSerializer, LoanSerializer


class LoanViewSet(ApiKeyProtectedViewMixin, viewsets.GenericViewSet):
    """
    list:
      GET /api/loans/?customer_external_id={external_id}
      Returns all loans, optionally filtered by customer.

    create:
      POST /api/loans/
      Creates a new loan with status=ACTIVE and outstanding=amount.

    retrieve:
      GET /api/loans/{external_id}/
      Returns a single loan by its external_id.

    activate:
      POST /api/loans/{external_id}/activate/
      Activates a pending loan.

    reject:
      POST /api/loans/{external_id}/reject/
      Rejects a pending loan.
    """

    queryset = Loan.objects.select_related("customer").all()
    lookup_field = "external_id"
    parser_classes = [JSONParser]

    def get_serializer_class(self):
        if self.action == "create":
            return LoanCreateSerializer
        return LoanSerializer

    @swagger_auto_schema(
        operation_summary="List Loans",
        operation_description=(
            "Optionally filter by passing "
            "`?customer_external_id=<external_id>` to only return loans for that customer."
        ),
        manual_parameters=[
            openapi.Parameter(
                "customer_external_id",
                openapi.IN_QUERY,
                description="External ID of the customer to filter by",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={200: LoanSerializer(many=True), 403: "Forbidden"},
    )
    def list(self, request):
        customer_id = request.query_params.get("customer_external_id")
        qs = self.get_queryset()
        if customer_id:
            qs = qs.filter(customer__external_id=customer_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Create Loan",
        operation_description=(
            "Creates a new loan. Validates that the customer's available credit is "
            "sufficient; on success, sets `status=ACTIVE` and `outstanding=amount`."
        ),
        request_body=LoanCreateSerializer,
        responses={201: LoanSerializer, 400: "Bad Request", 403: "Forbidden"},
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()
        output = LoanSerializer(loan)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Retrieve Loan",
        responses={200: LoanSerializer, 404: "Not Found", 403: "Forbidden"},
    )
    def retrieve(self, request, external_id=None):
        loan = self.get_object()
        serializer = self.get_serializer(loan)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Activate Loan",
        operation_description=(
            "Activate a pending loan: only allowed if status == PENDING. "
            "Sets status → ACTIVE and taken_at → now()."
        ),
        responses={
            200: LoanSerializer,
            400: "If the loan is not in PENDING status",
            403: "Forbidden",
        },
    )
    @action(detail=True, methods=["post"])
    def activate(self, request, external_id=None):
        loan = self.get_object()
        if loan.status != LoanStatus.PENDING:
            return Response(
                {"detail": "Only loans in 'pending' may be activated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        loan.status = LoanStatus.ACTIVE
        loan.taken_at = timezone.now()
        loan.save(update_fields=["status", "taken_at"])
        serializer = self.get_serializer(loan)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Reject Loan",
        operation_description=(
            "Reject a pending loan: only allowed if status == PENDING. "
            "Sets status → REJECTED."
        ),
        responses={
            204: "No Content on successful rejection",
            400: "If the loan is not in PENDING status",
            403: "Forbidden",
        },
    )
    @action(detail=True, methods=["post"])
    def reject(self, request, external_id=None):
        loan = self.get_object()
        if loan.status != LoanStatus.PENDING:
            return Response(
                {"detail": "Only loans in 'pending' may be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        loan.status = LoanStatus.REJECTED
        loan.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)
