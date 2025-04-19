# apps/customers/tests/test_customers.py

import csv
from io import StringIO

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_api_key.models import APIKey

from apps.customers.models.customers import Customer
from apps.loans.choices.loan_status import LoanStatus
from apps.loans.models.loans import Loan


class CustomerViewSetTests(APITestCase):
    """Test suite for the CustomerViewSet endpoints."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        # Create an API key and store it for authenticated requests
        _, self.api_key = APIKey.objects.create_key(name="test")
        self.base_url = "/customers/"

    def test_list_customers_initially_empty(self):
        """GET /customers/ returns an empty list when there are no customers."""
        response = self.client.get(self.base_url, HTTP_X_API_KEY=self.api_key)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    def test_create_customer_sets_active(self):
        """
        POST /customers/ with valid external_id and score:
        - Returns HTTP 201
        - Sets status to ACTIVE (1)
        - Leaves preapproved_at as None
        """
        payload = {"external_id": "cust_01", "score": "2500.00"}
        response = self.client.post(
            self.base_url, payload, format="json", HTTP_X_API_KEY=self.api_key
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["external_id"], "cust_01")
        self.assertEqual(response.data["score"], "2500.00")
        self.assertEqual(response.data["status"], 1)
        self.assertIsNone(response.data["preapproved_at"])

    def test_retrieve_customer(self):
        """
        GET /customers/{external_id}/ returns the customer data:
        - Matches the external_id and score of the created object.
        """
        customer = Customer.objects.create(external_id="cust_02", score=3000)
        response = self.client.get(
            f"{self.base_url}{customer.external_id}/", HTTP_X_API_KEY=self.api_key
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["external_id"], "cust_02")
        self.assertEqual(response.data["score"], "3000.00")

    def test_customer_balance_calculation(self):
        """
        GET /customers/{id}/balance/ computes:
        - total_debt: sum of outstanding on PENDING and ACTIVE loans
        - available_amount: score minus total_debt
        """
        customer = Customer.objects.create(external_id="cust_bal", score=5000)
        # Create one ACTIVE loan and one PENDING loan
        Loan.objects.create(
            external_id="loan_a",
            customer=customer,
            amount=2000,
            outstanding=2000,
            status=LoanStatus.ACTIVE,
            taken_at="2025-01-01T00:00:00Z",
            maximum_payment_date="2025-02-01T00:00:00Z",
        )
        Loan.objects.create(
            external_id="loan_b",
            customer=customer,
            amount=1000,
            outstanding=1000,
            status=LoanStatus.PENDING,
            taken_at="2025-01-10T00:00:00Z",
            maximum_payment_date="2025-03-10T00:00:00Z",
        )
        response = self.client.get(
            f"{self.base_url}{customer.external_id}/balance/", HTTP_X_API_KEY=self.api_key
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        # total_debt should be 2000 + 1000 = 3000
        self.assertEqual(data["total_debt"], "3000.00")
        # available_amount should be 5000 - 3000 = 2000
        self.assertEqual(data["available_amount"], "2000.00")

    @override_settings(USE_CELERY=False)
    def test_bulk_upload_customers_synchronous(self):
        """
        POST /customers/upload/ with a plain-text file (no Celery):
        - Parses lines: "external_id,score[,preapproved_at][,status]"
        - Returns 200 with dict containing "created" list and empty "errors"
        """
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["bulk_1", "1000.00", "2025-04-19T15:00:00Z", "1"])
        writer.writerow(["bulk_2", "2000.00", "2025-04-19T15:05:00Z", "1"])
        buffer.seek(0)

        response = self.client.post(
            f"{self.base_url}upload/",
            {"file": buffer},
            format="multipart",
            HTTP_X_API_KEY=self.api_key,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        # Both lines should have been created successfully
        self.assertIn("bulk_1", result["created"])
        self.assertIn("bulk_2", result["created"])
        self.assertEqual(result["errors"], [])

    def test_unauthorized_without_api_key(self):
        """
        Any endpoint without the X-API-KEY header should return 403 Forbidden.
        """
        # GET without API key
        resp = self.client.get(self.base_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        # POST without API key
        resp2 = self.client.post(
            self.base_url, {"external_id": "x", "score": "1.00"}, format="json"
        )
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_duplicate_external_id_fails(self):
        """
        Creating a customer with a duplicate external_id should return 400,
        with the error keyed on "external_id".
        """
        payload = {"external_id": "dup_01", "score": "100.00"}
        # First creation succeeds
        resp1 = self.client.post(
            self.base_url, payload, format="json", HTTP_X_API_KEY=self.api_key
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        # Second creation with the same external_id should fail
        resp2 = self.client.post(
            self.base_url, payload, format="json", HTTP_X_API_KEY=self.api_key
        )
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("external_id", resp2.data)
