from django.urls import include, path
from rest_framework import routers

from apps.payments.views.payments_view import PaymentViewSet

router = routers.DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
