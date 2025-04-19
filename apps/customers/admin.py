# apps/customers/admin.py
from django.contrib import admin

from apps.customers.models.customers import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "external_id",
        "status",
        "score",
        "preapproved_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("status",)
    search_fields = ("external_id",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
