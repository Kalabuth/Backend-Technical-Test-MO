from django.urls import include, path
from rest_framework import routers

from apps.loans.views.loan_view import LoanViewSet

router = routers.DefaultRouter()
router.register(r"loans", LoanViewSet, basename="loan")

urlpatterns = [
    path("", include(router.urls)),
]
