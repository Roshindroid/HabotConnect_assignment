from django.test import TestCase
from datetime import timedelta
from unittest.mock import Mock, patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Booking, LSAProfile, Parent, Payment
from .services.payment_service import (
    PaymentServiceError,
    initiate_payment,
)

# Create your tests here.

class BookingCreateAPITests(APITestCase):

    def setUp(self):
        self.parent = Parent.objects.create(
            name="Test Parent",
            email="parent@test.com",
        )

        self.lsa = LSAProfile.objects.create(
            name="Test LSA",
            email="lsa@test.com",
            skills=["autism", "adhd"],
            is_active=True,
        )

        self.url = reverse("booking-create")

        self.start_time = timezone.now() + timedelta(days=1)
        self.end_time = self.start_time + timedelta(hours=1)

    def test_valid_booking_returns_201(self):
        response = self.client.post(
            self.url,
            {
                "parent": self.parent.pk,
                "lsa": self.lsa.pk,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Booking.objects.count(),
            1,
        )

        self.assertEqual(
            response.data["status"],
            Booking.Status.PENDING,
        )

    def test_invalid_time_range_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "parent": self.parent.pk,
                "lsa": self.lsa.pk,
                "start_time": self.end_time.isoformat(),
                "end_time": self.start_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Booking.objects.count(),
            0,
        )

    def test_overlapping_booking_returns_400(self):
        Booking.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            start_time=self.start_time,
            end_time=self.end_time,
            status=Booking.Status.PENDING,
        )

        overlapping_start = self.start_time + timedelta(minutes=30)
        overlapping_end = self.end_time + timedelta(minutes=30)

        response = self.client.post(
            self.url,
            {
                "parent": self.parent.pk,
                "lsa": self.lsa.pk,
                "start_time": overlapping_start.isoformat(),
                "end_time": overlapping_end.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Booking.objects.count(),
            1,
        )
        
class LSASearchAPITests(APITestCase):

    def setUp(self):
        self.parent = Parent.objects.create(
            name="Test Parent",
            email="search-parent@test.com",
        )

        self.available_lsa = LSAProfile.objects.create(
            name="Available LSA",
            email="available@test.com",
            skills=["autism", "adhd"],
            is_active=True,
        )

        self.wrong_skill_lsa = LSAProfile.objects.create(
            name="Wrong Skill LSA",
            email="wrong-skill@test.com",
            skills=["dyslexia"],
            is_active=True,
        )

        self.inactive_lsa = LSAProfile.objects.create(
            name="Inactive LSA",
            email="inactive@test.com",
            skills=["autism"],
            is_active=False,
        )

        self.url = reverse("lsa-search")

        self.start_time = timezone.now() + timedelta(days=2)
        self.end_time = self.start_time + timedelta(hours=1)

    def test_matching_available_lsa_is_returned(self):
        response = self.client.get(
            self.url,
            {
                "skill": "autism",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = [
            lsa["id"]
            for lsa in response.data
        ]

        self.assertIn(
            self.available_lsa.pk,
            returned_ids,
        )

    def test_wrong_skill_lsa_is_not_returned(self):
        response = self.client.get(
            self.url,
            {
                "skill": "autism",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
            },
        )

        returned_ids = [
            lsa["id"]
            for lsa in response.data
        ]

        self.assertNotIn(
            self.wrong_skill_lsa.pk,
            returned_ids,
        )

    def test_inactive_lsa_is_not_returned(self):
        response = self.client.get(
            self.url,
            {
                "skill": "autism",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
            },
        )

        returned_ids = [
            lsa["id"]
            for lsa in response.data
        ]

        self.assertNotIn(
            self.inactive_lsa.pk,
            returned_ids,
        )

    def test_booked_lsa_is_not_returned(self):
        Booking.objects.create(
            parent=self.parent,
            lsa=self.available_lsa,
            start_time=self.start_time,
            end_time=self.end_time,
            status=Booking.Status.PENDING,
        )

        response = self.client.get(
            self.url,
            {
                "skill": "autism",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
            },
        )

        returned_ids = [
            lsa["id"]
            for lsa in response.data
        ]

        self.assertNotIn(
            self.available_lsa.pk,
            returned_ids,
        )
        
class PaymentWebhookAPITests(APITestCase):

    def setUp(self):
        self.parent = Parent.objects.create(
            name="Payment Parent",
            email="payment-parent@test.com",
        )

        self.lsa = LSAProfile.objects.create(
            name="Payment LSA",
            email="payment-lsa@test.com",
            skills=["autism"],
            is_active=True,
        )

        self.booking = Booking.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            start_time=timezone.now() + timedelta(days=3),
            end_time=timezone.now() + timedelta(days=3, hours=1),
            status=Booking.Status.PENDING,
        )

        self.url = reverse("payment-webhook")

    def test_successful_payment_confirms_booking(self):
        response = self.client.post(
            self.url,
            {
                "booking_id": self.booking.pk,
                "transaction_id": "TEST-TXN-SUCCESS",
                "status": "SUCCESS",
                "amount": "500.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.CONFIRMED,
        )

        payment = Payment.objects.get(
            booking=self.booking
        )

        self.assertEqual(
            payment.status,
            Payment.Status.SUCCESS,
        )

        self.assertEqual(
            payment.transaction_id,
            "TEST-TXN-SUCCESS",
        )

    def test_failed_payment_marks_booking_failed(self):
        response = self.client.post(
            self.url,
            {
                "booking_id": self.booking.pk,
                "transaction_id": "TEST-TXN-FAILED",
                "status": "FAILED",
                "amount": "500.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.PAYMENT_FAILED,
        )

        payment = Payment.objects.get(
            booking=self.booking
        )

        self.assertEqual(
            payment.status,
            Payment.Status.FAILED,
        )

    def test_invalid_booking_returns_404(self):
        response = self.client.post(
            self.url,
            {
                "booking_id": 999999,
                "transaction_id": "TEST-TXN-INVALID",
                "status": "SUCCESS",
                "amount": "500.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
    
    def test_duplicate_success_webhook_is_idempotent(self):
        payload = {
            "booking_id": self.booking.pk,
            "transaction_id": "IDEMPOTENCY-TEST-001",
            "status": "SUCCESS",
            "amount": "500.00",
        }

        first_response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        second_response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            second_response.data["message"],
            "Payment webhook already processed.",
        )

        self.assertEqual(
            Payment.objects.filter(
                booking=self.booking
            ).count(),
            1,
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.CONFIRMED,
        )
        
class PaymentServiceTests(APITestCase):

    def setUp(self):
        self.parent = Parent.objects.create(
            name="Service Parent",
            email="service-parent@test.com",
        )

        self.lsa = LSAProfile.objects.create(
            name="Service LSA",
            email="service-lsa@test.com",
            skills=["autism"],
            is_active=True,
        )

        self.booking = Booking.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            start_time=timezone.now() + timedelta(days=4),
            end_time=timezone.now() + timedelta(days=4, hours=1),
            status=Booking.Status.PENDING,
        )

    @patch("bookings.services.payment_service.requests.post")
    def test_successful_payment_request(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "status": "SUCCESS",
            "transaction_id": "MOCK-TXN-001",
        }

        mock_post.return_value = mock_response

        result = initiate_payment(
            self.booking,
            "500.00",
        )

        self.assertEqual(
            result["status"],
            "SUCCESS",
        )

        mock_post.assert_called_once_with(
            "https://mock-payment-service.example/pay",
            json={
                "booking_id": self.booking.pk,
                "amount": "500.00",
            },
            timeout=5,
        )

    @patch("bookings.services.payment_service.requests.post")
    def test_payment_request_failure_raises_error(self, mock_post):
        from requests.exceptions import Timeout

        mock_post.side_effect = Timeout(
            "Payment service timed out"
        )

        with self.assertRaises(PaymentServiceError):
            initiate_payment(
                self.booking,
                "500.00",
            )

        mock_post.assert_called_once()