from rest_framework.views import APIView

from apps.authentication.methods.authentication_config import (
    add_api_permission_to_permission_classes,
)


class ApiKeyProtectedViewMixin(APIView):
    """
    Mixin to add api key protection to views

    This can be used in any view with APIView as parent class such as:
    - APIView
    - GenericAPIView
    - ViewSet
    - GenericViewSet
    - ModelViewSet
    """

    def check_permissions(self, request):
        permissions = add_api_permission_to_permission_classes(self.get_permissions())
        for permission in permissions:
            if not permission.has_permission(request=request, view=self):
                self.permission_denied(
                    request, message=getattr(permission, "message", None)
                )
