"""
Swagger configuration

This file is used to configure the swagger documentation for the API.
"""

# Django lib
from django.conf import settings

# Third party libs
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

# Rest Framework
from rest_framework import permissions

ALLOWED_PERMISSIONS = {
    "Authenticated": permissions.IsAuthenticated,
    "Admin": permissions.IsAdminUser,
    "Any": permissions.AllowAny,
}

permission = ALLOWED_PERMISSIONS.get(settings.SWAGGER_PERMISSIONS, permissions.AllowAny)

schema_view = get_schema_view(
    openapi.Info(
        title="Mo API",
        default_version="v1",
        description="Description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="juancamiloariascalderon173@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permission,),
)
