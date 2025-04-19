# apps/payments/admin.py
from django.contrib import admin

from apps.payments.models.payment import Payment
from apps.payments.models.payment_detail import PaymentDetail


class PaymentDetailInline(admin.TabularInline):
    model = PaymentDetail
    extra = 0
    readonly_fields = ("loan", "amount")
    can_delete = False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "external_id",
        "customer",
        "total_amount",
        "status",
        "paid_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "paid_at")
    search_fields = ("external_id", "customer__external_id")
    list_select_related = ("customer",)
    inlines = [PaymentDetailInline]
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-paid_at",)


@admin.register(PaymentDetail)
class PaymentDetailAdmin(admin.ModelAdmin):
    list_display = ("payment", "loan", "amount")
    list_select_related = ("payment", "loan")
    search_fields = ("payment__external_id", "loan__external_id")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("payment", "loan")
