from typing import List

from rest_framework_api_key.permissions import HasAPIKey


def add_api_permission_to_permission_classes(permissions: List):
    """
    Adds ApiKey class to base auth permissions
    """
    permissions = [HasAPIKey()] + permissions

    return permissions
