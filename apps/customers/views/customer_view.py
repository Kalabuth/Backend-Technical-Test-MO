from django.db import transaction
from django.db.models import Sum
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.authentication.mixins.api_key_protected_view_mixin import (
    ApiKeyProtectedViewMixin,
)
from apps.common.methods.custom_pagination import CustomPagination
from apps.customers.models.customers import Customer
from apps.customers.serializers.customer_serializer import (
    CustomerBalanceSerializer,
    CustomerSerializer,
    CustomerUploadSerializer,
)
from mo.task_handler import handle_task


class CustomerViewSet(ApiKeyProtectedViewMixin, GenericViewSet):
    """
    retrieve:
      GET /api/customers/{external_id}/       Retrieve a single customer.
    list:
      GET /api/customers/                     List all customers.
    create:
      POST /api/customers/                    Create a new customer.
    upload:
      POST /api/customers/upload/             Bulk import customers via file.
    balance:
      GET /api/customers/{external_id}/balance/  Get total debt & available credit.
    """

    queryset = Customer.objects.all().order_by("-created_at")
    lookup_field = "external_id"
    parser_classes = [JSONParser, MultiPartParser]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "upload":
            return CustomerUploadSerializer
        if self.action == "balance":
            return CustomerBalanceSerializer
        return CustomerSerializer

    @swagger_auto_schema(
        operation_summary="List Customers", responses={200: CustomerSerializer(many=True)}
    )
    def list(self, request):
        customers = self.get_queryset()
        page = self.paginate_queryset(customers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Create Customer",
        request_body=CustomerSerializer,
        responses={201: CustomerSerializer, 400: "Bad Request"},
    )
    @transaction.atomic
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return Response(
            self.get_serializer(customer).data, status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_summary="Retrieve Customer",
        responses={200: CustomerSerializer, 404: "Not Found"},
    )
    def retrieve(self, request, external_id=None):
        customer = self.get_object()
        serializer = self.get_serializer(customer)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Bulk import customers via file",
        request_body=None,
        manual_parameters=[
            openapi.Parameter(
                name="file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Plain‑text file where each line is `external_id,score`",
                required=True,
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "created": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_STRING),
                    ),
                    "errors": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_STRING),
                    ),
                },
            ),
            202: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"task_id": openapi.Schema(type=openapi.TYPE_STRING)},
            ),
            400: "Bad Request",
        },
        consumes=["multipart/form-data"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="upload",
        parser_classes=[MultiPartParser],
    )
    def upload(self, request):
        upload_ser = self.get_serializer(data=request.data)
        upload_ser.is_valid(raise_exception=True)

        raw = upload_ser.validated_data["file"].read().decode("utf-8")
        result = handle_task(
            module="apps.customers.tasks",
            function="import_customers_task",
            queue="default",
            raw_content=raw,
        )

        if isinstance(result, dict):
            return Response(result, status=status.HTTP_200_OK)

        return Response({"task_id": result.id}, status=status.HTTP_202_ACCEPTED)

    @swagger_auto_schema(
        operation_summary="Get Customer Balance",
        responses={200: CustomerBalanceSerializer, 404: "Not Found"},
    )
    @action(detail=True, methods=["get"])
    def balance(self, request, external_id=None):
        customer = self.get_object()
        agg = customer.loans.filter(status__in=[1, 2]).aggregate(
            total_debt=Sum("outstanding")
        )
        total_debt = agg["total_debt"] or 0
        available = customer.score - total_debt
        payload = {
            "external_id": customer.external_id,
            "score": customer.score,
            "total_debt": total_debt,
            "available_amount": available,
        }
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
