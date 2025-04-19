from django.db.models import (
    PROTECT,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    IntegerField,
)

from apps.common.models.base_model import BaseModel
from apps.customers.models.customers import Customer
from apps.payments.choices.payment_status_choices import PaymentStatus


class Payment(BaseModel):
    external_id = CharField(max_length=60, unique=True)
    total_amount = DecimalField(max_digits=20, decimal_places=10)
    status = IntegerField(
        choices=PaymentStatus.choices,
        default=PaymentStatus.COMPLETED,
    )
    paid_at = DateTimeField(null=True, blank=True)
    customer = ForeignKey(Customer, on_delete=PROTECT, related_name="payments")

    def __str__(self):
        return f"Payment {self.external_id} – ${self.total_amount}"
