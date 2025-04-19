from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from apps.customers.models.customers import Customer
from apps.loans.choices.loan_status import LoanStatus
from apps.payments.choices.payment_status_choices import PaymentStatus
from apps.payments.models.payment import Payment
from apps.payments.models.payment_detail import PaymentDetail


class PaymentDetailReadSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura para el detalle de cada pago por préstamo.
    """

    loan_external_id = serializers.CharField(source="loan.external_id", read_only=True)
    amount = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = PaymentDetail
        fields = ["loan_external_id", "amount"]


class PaymentReadSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura para Payment, con detalles anidados.
    """

    customer_external_id = serializers.CharField(
        source="customer.external_id", read_only=True
    )
    payment_details = PaymentDetailReadSerializer(
        source="details", many=True, read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "external_id",
            "customer_external_id",
            "total_amount",
            "status",
            "paid_at",
            "payment_details",
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación de Payment con reparto automático:
      - Si total_amount > deuda total → status=REJECTED.
      - Si total_amount ≤ deuda total:
          * status=COMPLETED, paid_at=ahora.
          * Distribuye en FIFO (por taken_at asc) hasta agotar el monto.
          * Crea PaymentDetail y actualiza outstanding/status de cada Loan.
    """

    customer_external_id = serializers.SlugRelatedField(
        source="customer", slug_field="external_id", queryset=Customer.objects.all()
    )

    class Meta:
        model = Payment
        fields = ["external_id", "customer_external_id", "total_amount"]
        read_only_fields = ["status", "paid_at"]

    def validate(self, data):
        customer = data["customer"]
        total_amount = data["total_amount"]

        # 1) Calcula la deuda total pendiente
        total_debt = (
            customer.loans.filter(
                status__in=[LoanStatus.PENDING, LoanStatus.ACTIVE]
            ).aggregate(debt=Sum("outstanding"))["debt"]
            or 0
        )

        # 2) Permite pasar a create(), donde se registrará REJECTED o COMPLETED
        if total_amount > total_debt:
            return data

        # 3) Si total_amount ≤ deuda total, está OK
        return data

    def create(self, validated_data):
        customer = validated_data["customer"]
        total_amount = validated_data["total_amount"]
        external_id = validated_data["external_id"]

        # Recalculamos deuda para evitar race conditions
        total_debt = (
            customer.loans.filter(
                status__in=[LoanStatus.PENDING, LoanStatus.ACTIVE]
            ).aggregate(debt=Sum("outstanding"))["debt"]
            or 0
        )

        # 1) Si excede deuda total → REJECTED
        if total_amount > total_debt:
            return Payment.objects.create(
                external_id=external_id,
                customer=customer,
                total_amount=total_amount,
                status=PaymentStatus.REJECTED,
                # paid_at queda NULL
            )

        # 2) Pago válido → COMPLETED
        payment = Payment.objects.create(
            external_id=external_id,
            customer=customer,
            total_amount=total_amount,
            status=PaymentStatus.COMPLETED,
            paid_at=timezone.now(),
        )

        # 3) Reparto FIFO por taken_at
        remaining = total_amount
        loans = customer.loans.filter(
            status__in=[LoanStatus.PENDING, LoanStatus.ACTIVE]
        ).order_by("taken_at")
        for loan in loans:
            if remaining <= 0:
                break

            to_apply = min(loan.outstanding, remaining)
            # guardamos detalle
            PaymentDetail.objects.create(payment=payment, loan=loan, amount=to_apply)
            # actualizamos préstamo
            loan.outstanding -= to_apply
            if loan.outstanding == 0:
                loan.status = LoanStatus.PAID
            else:
                loan.status = LoanStatus.ACTIVE
            loan.save(update_fields=["outstanding", "status"])

            remaining -= to_apply

        return payment
