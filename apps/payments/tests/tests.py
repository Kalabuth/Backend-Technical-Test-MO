from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_api_key.models import APIKey

from apps.customers.choices.customer_status import CustomerStatus
from apps.customers.models.customers import Customer
from apps.loans.choices.loan_status import LoanStatus
from apps.loans.models.loans import Loan
from apps.payments.choices.payment_status_choices import PaymentStatus
from apps.payments.models.payment import Payment


class PaymentViewSetTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        _, self.api_key = APIKey.objects.create_key(name="test")
        self.auth = {"HTTP_X_API_KEY": self.api_key}

        # Create a customer with ACTIVE status
        self.customer = Customer.objects.create(
            external_id="cust_pay", score=1000, status=CustomerStatus.ACTIVE
        )
        # Create two active loans for that customer
        self.loan1 = Loan.objects.create(
            external_id="loan_x",
            customer=self.customer,
            amount=600,
            outstanding=600,
            status=LoanStatus.ACTIVE,
            taken_at="2025-04-01T00:00:00Z",
            maximum_payment_date="2025-05-01T00:00:00Z",
        )
        self.loan2 = Loan.objects.create(
            external_id="loan_y",
            customer=self.customer,
            amount=400,
            outstanding=400,
            status=LoanStatus.ACTIVE,
            taken_at="2025-04-02T00:00:00Z",
            maximum_payment_date="2025-05-02T00:00:00Z",
        )

        self.url = "/payments/"

    def test_create_payment_success_auto_distribution(self):
        """
        POST /payments/ with total_amount=700.00:
        - Automatically distributes 600.00 to loan_x (marking it PAID, outstanding=0)
        - Distributes the remaining 100.00 to loan_y (leaving outstanding=300.00, status ACTIVE)
        - Returns HTTP 201 and status COMPLETED.
        """
        payload = {
            "external_id": "pay_01",
            "customer_external_id": self.customer.external_id,
            "total_amount": "700.00",
        }
        resp = self.client.post(self.url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.data
        self.assertEqual(data["status"], PaymentStatus.COMPLETED)

        # Verify payment details breakdown
        details = {d["loan_external_id"]: d["amount"] for d in data["payment_details"]}
        self.assertEqual(details, {"loan_x": "600.00", "loan_y": "100.00"})

        # Verify each loan was updated correctly
        self.loan1.refresh_from_db()
        self.loan2.refresh_from_db()
        self.assertEqual(self.loan1.outstanding, 0)
        self.assertEqual(self.loan1.status, LoanStatus.PAID)
        self.assertEqual(self.loan2.outstanding, 300)
        self.assertEqual(self.loan2.status, LoanStatus.ACTIVE)

    def test_create_payment_exceeds_total_debt(self):
        """
        POST /payments/ with total_amount exceeding total customer debt:
        - Creates a payment with status REJECTED
        - No payment details are recorded
        - Loans remain unchanged
        - Returns HTTP 201.
        """
        payload = {
            "external_id": "pay_02",
            "customer_external_id": self.customer.external_id,
            "total_amount": "1200.00",  # total debt is only 1000
        }
        resp = self.client.post(self.url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.data
        self.assertEqual(data["status"], PaymentStatus.REJECTED)
        self.assertEqual(data["payment_details"], [])

        # Loans should be untouched
        self.loan1.refresh_from_db()
        self.loan2.refresh_from_db()
        self.assertEqual(self.loan1.outstanding, 600)
        self.assertEqual(self.loan2.outstanding, 400)

    def test_list_and_retrieve_payments(self):
        """
        GET /payments/?customer_external_id=… and GET /payments/{external_id}/
        should list and retrieve payments properly.
        """
        # Create a completed payment record directly
        p = Payment.objects.create(
            external_id="pay_list",
            customer=self.customer,
            total_amount=500,
            status=PaymentStatus.COMPLETED,
        )
        # List
        resp_list = self.client.get(
            f"{self.url}?customer_external_id={self.customer.external_id}", **self.auth
        )
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        self.assertIn("pay_list", [x["external_id"] for x in resp_list.data])

        # Retrieve detail
        resp_det = self.client.get(f"{self.url}{p.external_id}/", **self.auth)
        self.assertEqual(resp_det.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_det.data["external_id"], p.external_id)
