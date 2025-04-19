from django.db.models import Sum
from rest_framework import serializers

from apps.customers.models.customers import Customer
from apps.loans.models.loans import Loan, LoanStatus


class LoanSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Loan instances.
    Exposes:
      - external_id
      - customer_external_id
      - amount
      - outstanding
      - status
      - contract_version
      - taken_at
      - maximum_payment_date
    """

    customer_external_id = serializers.CharField(
        source="customer.external_id", read_only=True
    )

    class Meta:
        model = Loan
        fields = [
            "external_id",
            "customer_external_id",
            "amount",
            "outstanding",
            "status",
            "contract_version",
            "taken_at",
            "maximum_payment_date",
        ]


class LoanCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new Loan instances.
    - Validates that existing debt + new amount <= customer.score
    - On create, sets status=PENDING (1) and outstanding=amount
    """

    customer_external_id = serializers.SlugRelatedField(
        source="customer", slug_field="external_id", queryset=Customer.objects.all()
    )

    class Meta:
        model = Loan
        fields = [
            "external_id",
            "customer_external_id",
            "amount",
            "contract_version",
            "taken_at",
            "maximum_payment_date",
        ]
        # status and outstanding are set in create(), so we do not expose them here
        read_only_fields = []

    def validate_amount(self, value):
        """
        Ensure new loan amount plus all existing pending/active outstanding
        does not exceed the customer's credit line (score).
        """
        customer = self.initial_data.get("customer_external_id")
        customer_instance = Customer.objects.filter(external_id=customer).first()
        if customer_instance is None:
            raise serializers.ValidationError(
                "Customer with that external_id does not exist."
            )

        aggregate = customer_instance.loans.filter(status__in=[1, 2]).aggregate(
            total_outstanding=Sum("outstanding")
        )
        existing_debt = aggregate["total_outstanding"] or 0

        if existing_debt + value > customer_instance.score:
            raise serializers.ValidationError(
                "This loan would exceed the customer's available credit line."
            )
        return value

    def create(self, validated_data):
        """
        Create the Loan with:
          - status = PENDING (1)
          - outstanding = amount
        """
        loan_instance = Loan.objects.create(
            external_id=validated_data["external_id"],
            customer=validated_data["customer"],
            amount=validated_data["amount"],
            outstanding=validated_data["amount"],
            status=LoanStatus.PENDING,
            contract_version=validated_data.get("contract_version", ""),
            taken_at=validated_data.get("taken_at"),
            maximum_payment_date=validated_data.get("maximum_payment_date"),
        )
        return loan_instance
