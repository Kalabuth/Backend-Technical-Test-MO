from rest_framework.test import APIClient
from rest_framework_api_key.models import APIKey


class ApiKeyTestMixin:
    def setUp(self):
        api_key_obj, api_key = APIKey.objects.create_key(name="test-key")
        self.api_key = api_key
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
