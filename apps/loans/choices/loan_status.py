from django.db.models import IntegerChoices


class LoanStatus(IntegerChoices):
    PENDING = 1, "Pending"
    ACTIVE = 2, "Active"
    REJECTED = 3, "Rejected"
    PAID = 4, "Paid"
