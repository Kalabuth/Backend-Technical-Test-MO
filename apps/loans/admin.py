# apps/loans/admin.py
from django.contrib import admin

from apps.loans.models.loans import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "external_id",
        "customer",
        "amount",
        "outstanding",
        "status",
        "taken_at",
        "maximum_payment_date",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "customer", "taken_at")
    search_fields = ("external_id", "customer__external_id")
    list_select_related = ("customer",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-taken_at",)
