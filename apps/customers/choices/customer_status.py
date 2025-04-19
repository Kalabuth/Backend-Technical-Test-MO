from django.db.models import IntegerChoices


class CustomerStatus(IntegerChoices):
    ACTIVE = 1, "Active"
    INACTIVE = 2, "Inactive"
