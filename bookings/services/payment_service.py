import logging

import requests


logger = logging.getLogger(__name__)


class PaymentServiceError(Exception):
    """Raised when the payment service cannot be reached or fails."""


def initiate_payment(booking, amount):
    payment_url = "https://mock-payment-service.example/pay"

    payload = {
        "booking_id": booking.pk,
        "amount": str(amount),
    }

    try:
        response = requests.post(
            payment_url,
            json=payload,
            timeout=5,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:
        logger.exception(
            "Payment service request failed for booking %s",
            booking.pk,
        )

        raise PaymentServiceError(
            "Unable to process payment."
        ) from exc