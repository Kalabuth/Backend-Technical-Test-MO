# apps/loans/tests/test_loans.py

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_api_key.models import APIKey

from apps.customers.models.customers import Customer
from apps.loans.models.loans import Loan, LoanStatus


class LoanViewSetTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        _, self.api_key = APIKey.objects.create_key(name="test")
        self.auth = {"HTTP_X_API_KEY": self.api_key}
        self.url = "/loans/"

        self.customer = Customer.objects.create(external_id="cust_loan", score=1000)

    def test_create_loan_within_credit(self):
        """
        POST /loans/ with amount=500 and dates should create a loan with
        status ACTIVE (2) and outstanding equal to the requested amount.
        """
        payload = {
            "external_id": "loan_01",
            "customer_external_id": self.customer.external_id,
            "amount": "500.00",
            "contract_version": "v1",
            "taken_at": "2025-04-01T00:00:00Z",
            "maximum_payment_date": "2025-05-01T00:00:00Z",
        }
        resp = self.client.post(self.url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.data
        self.assertEqual(data["external_id"], "loan_01")
        self.assertEqual(data["outstanding"], "500.00")
        self.assertEqual(data["status"], LoanStatus.ACTIVE)

    def test_create_loan_exceeds_credit_fails(self):
        """
        POST /loans/ with amount > score should return 400
        with an appropriate error message.
        """
        payload = {
            "external_id": "loan_fail",
            "customer_external_id": self.customer.external_id,
            "amount": "1500.00",
        }
        resp = self.client.post(self.url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        msg = resp.data["amount"][0].lower()
        self.assertIn("exceed the customer's available credit line", msg)

    def test_list_and_retrieve_loans(self):
        """
        GET /loans/?customer_external_id=… and GET /loans/{id}/
        should list and retrieve loans correctly.
        """
        loan_a = Loan.objects.create(
            external_id="loan_a",
            customer=self.customer,
            amount=100,
            outstanding=100,
            status=LoanStatus.ACTIVE,
            taken_at="2025-04-01T00:00:00Z",
            maximum_payment_date="2025-05-01T00:00:00Z",
        )
        Loan.objects.create(
            external_id="loan_b",
            customer=self.customer,
            amount=200,
            outstanding=200,
            status=LoanStatus.ACTIVE,
            taken_at="2025-04-02T00:00:00Z",
            maximum_payment_date="2025-05-02T00:00:00Z",
        )

        # list
        resp_list = self.client.get(
            f"{self.url}?customer_external_id={self.customer.external_id}", **self.auth
        )
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        ext_ids = {item["external_id"] for item in resp_list.data}
        self.assertEqual(ext_ids, {"loan_a", "loan_b"})

        # retrieve
        resp_det = self.client.get(f"{self.url}{loan_a.external_id}/", **self.auth)
        self.assertEqual(resp_det.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_det.data["external_id"], loan_a.external_id)

    def test_activate_pending_loan(self):
        """
        POST /loans/{id}/activate/ should only work when the loan is
        in PENDING (1), updating status to ACTIVE (2) and setting taken_at
        to the current time.
        """
        loan = Loan.objects.create(
            external_id="loan_pend",
            customer=self.customer,
            amount=300,
            outstanding=300,
            status=LoanStatus.PENDING,
            taken_at=None,
            maximum_payment_date="2025-06-01T00:00:00Z",
        )
        before = timezone.now()
        resp = self.client.post(f"{self.url}{loan.external_id}/activate/", **self.auth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        loan.refresh_from_db()
        self.assertEqual(loan.status, LoanStatus.ACTIVE)
        self.assertIsNotNone(loan.taken_at)
        self.assertGreaterEqual(loan.taken_at, before)

    def test_activate_non_pending_loan_fails(self):
        """
        POST /loans/{id}/activate/ on a non-PENDING loan should return 400.
        """
        loan = Loan.objects.create(
            external_id="loan_active",
            customer=self.customer,
            amount=100,
            outstanding=100,
            status=LoanStatus.ACTIVE,
            taken_at="2025-04-01T00:00:00Z",
            maximum_payment_date="2025-05-01T00:00:00Z",
        )
        resp = self.client.post(f"{self.url}{loan.external_id}/activate/", **self.auth)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "only loans in 'pending' may be activated", resp.data["detail"].lower()
        )

    def test_reject_pending_loan(self):
        """
        POST /loans/{id}/reject/ on a PENDING loan should change
        its status to REJECTED (3) and return 204 No Content.
        """
        loan = Loan.objects.create(
            external_id="loan_pend2",
            customer=self.customer,
            amount=250,
            outstanding=250,
            status=LoanStatus.PENDING,
            taken_at=None,
            maximum_payment_date="2025-06-01T00:00:00Z",
        )
        resp = self.client.post(f"{self.url}{loan.external_id}/reject/", **self.auth)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        loan.refresh_from_db()
        self.assertEqual(loan.status, LoanStatus.REJECTED)

    def test_reject_non_pending_fails(self):
        """
        POST /loans/{id}/reject/ on a non-PENDING loan should return 400.
        """
        loan = Loan.objects.create(
            external_id="loan_paid",
            customer=self.customer,
            amount=150,
            outstanding=0,
            status=LoanStatus.PAID,
            taken_at="2025-04-01T00:00:00Z",
            maximum_payment_date="2025-05-01T00:00:00Z",
        )
        resp = self.client.post(f"{self.url}{loan.external_id}/reject/", **self.auth)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "only loans in 'pending' may be rejected", resp.data["detail"].lower()
        )

    def test_unauthorized_without_api_key(self):
        """
        Without X-API-KEY header, all endpoints should return 403 Forbidden.
        """
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        # activate
        loan = Loan.objects.create(
            external_id="loan_xx",
            customer=self.customer,
            amount=100,
            outstanding=100,
            status=LoanStatus.PENDING,
            taken_at=None,
            maximum_payment_date="2025-05-01T00:00:00Z",
        )
        resp2 = self.client.post(f"{self.url}{loan.external_id}/activate/")
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)
        # reject
        resp3 = self.client.post(f"{self.url}{loan.external_id}/reject/")
        self.assertEqual(resp3.status_code, status.HTTP_403_FORBIDDEN)
