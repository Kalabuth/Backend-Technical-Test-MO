from django.db.models import CharField, DateTimeField, DecimalField, SmallIntegerField

from apps.common.models.base_model import BaseModel
from apps.customers.choices.customer_status import CustomerStatus


class Customer(BaseModel):
    external_id = CharField(max_length=60, unique=True)
    status = SmallIntegerField(
        choices=CustomerStatus.choices,
        default=CustomerStatus.ACTIVE,
    )
    score = DecimalField(max_digits=12, decimal_places=2)
    preapproved_at = DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Customer {self.external_id} (status={self.status})"
