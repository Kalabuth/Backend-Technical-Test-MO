from django.db.models import CASCADE, DecimalField, ForeignKey

from apps.common.models.base_model import BaseModel
from apps.loans.models.loans import Loan
from apps.payments.models.payment import Payment


class PaymentDetail(BaseModel):
    amount = DecimalField(max_digits=20, decimal_places=2)
    loan = ForeignKey(Loan, on_delete=CASCADE, related_name="payment_details")
    payment = ForeignKey(Payment, on_delete=CASCADE, related_name="details")

    def __str__(self):
        return (
            f"Detail: ${self.amount} for Loan {self.loan.external_id} "
            f"(Payment {self.payment.external_id})"
        )
