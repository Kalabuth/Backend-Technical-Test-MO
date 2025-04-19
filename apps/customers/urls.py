from django.urls import include, path
from rest_framework import routers

from apps.customers.views.customer_view import CustomerViewSet

router = routers.DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customer")

urlpatterns = [
    path("", include(router.urls)),
]
