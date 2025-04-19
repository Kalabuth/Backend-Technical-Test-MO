from django.db.models import IntegerChoices


class PaymentStatus(IntegerChoices):
    COMPLETED = 1, "Completed"
    REJECTED = 2, "Rejected"
