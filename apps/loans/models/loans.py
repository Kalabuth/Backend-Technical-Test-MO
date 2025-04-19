from django.db.models import (
    PROTECT,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    SmallIntegerField,
)

from apps.common.models.base_model import BaseModel
from apps.customers.models.customers import Customer
from apps.loans.choices.loan_status import LoanStatus


class Loan(BaseModel):
    external_id = CharField(max_length=60, unique=True)
    amount = DecimalField(max_digits=12, decimal_places=2)
    status = SmallIntegerField(choices=LoanStatus.choices, default=LoanStatus.PENDING)
    contract_version = CharField(max_length=30)
    maximum_payment_date = DateTimeField()
    taken_at = DateTimeField(null=True, blank=True)
    outstanding = DecimalField(max_digits=12, decimal_places=2)
    customer = ForeignKey(Customer, on_delete=PROTECT, related_name="loans")

    def __str__(self):
        return f"Loan {self.external_id} – Customer {self.customer.external_id}"
