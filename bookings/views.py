import logging
from django.shortcuts import render
from django.db import transaction
from django.db.models import Exists, OuterRef

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, LSAProfile, Payment
from .serializers import BookingSerializer, LSAProfileSerializer

# Create your views here.

logger = logging.getLogger(__name__)

class BookingCreateView(APIView):

    @transaction.atomic
    def post(self, request):
        serializer = BookingSerializer(data=request.data)

        if serializer.is_valid():
            booking = serializer.save()
            
            logger.info(
                "Booking created successfully: booking_id=%s parent_id=%s lsa_id=%s",
                booking.pk,
                booking.parent_id,
                booking.lsa_id,
            )

            return Response(
                BookingSerializer(booking).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LSASearchView(APIView):

    def get(self, request):
        skill = request.query_params.get("skill")
        start_time = request.query_params.get("start_time")
        end_time = request.query_params.get("end_time")

        if not skill:
            return Response(
                {"error": "skill parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not start_time or not end_time:
            return Response(
                {
                    "error": (
                        "start_time and end_time parameters "
                        "are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        overlapping_bookings = Booking.objects.filter(
            lsa=OuterRef("pk"),
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exclude(
            status__in=[
                Booking.Status.CANCELLED,
                Booking.Status.PAYMENT_FAILED,
            ]
        )

        lsas = LSAProfile.objects.filter(
            is_active=True
        ).annotate(
            has_overlap=Exists(overlapping_bookings)
        ).filter(
            has_overlap=False
        )

        matching_lsas = [
            lsa for lsa in lsas
            if skill.lower() in [
                item.lower() for item in lsa.skills
            ]
        ]

        serializer = LSAProfileSerializer(
            matching_lsas,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
        
        
class PaymentWebhookView(APIView):

    @transaction.atomic
    def post(self, request):
        booking_id = request.data.get("booking_id")
        transaction_id = request.data.get("transaction_id")
        payment_status = request.data.get("status")
        amount = request.data.get("amount")

        if not booking_id or not transaction_id or not payment_status:
            return Response(
                {"error": "Invalid payment webhook payload."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking = Booking.objects.get(pk=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        existing_payment = Payment.objects.filter(
            booking=booking
        ).first()

        if existing_payment:
            if (
                existing_payment.status == Payment.Status.SUCCESS
                and payment_status == "SUCCESS"
            ):
                return Response(
                    {
                        "message": "Payment webhook already processed.",
                        "booking_id": booking.pk,
                        "payment_id": existing_payment.pk,
                        "booking_status": booking.status,
                    },
                    status=status.HTTP_200_OK
                )

            if (
                existing_payment.status == Payment.Status.FAILED
                and payment_status == "FAILED"
            ):
                return Response(
                    {
                        "message": "Payment webhook already processed.",
                        "booking_id": booking.pk,
                        "payment_id": existing_payment.pk,
                        "booking_status": booking.status,
                    },
                    status=status.HTTP_200_OK
                )

        if payment_status == "SUCCESS":
            payment, _ = Payment.objects.update_or_create(
                booking=booking,
                defaults={
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "status": Payment.Status.SUCCESS,
                },
            )

            booking.status = Booking.Status.CONFIRMED
            booking.save(update_fields=["status"])
            
            logger.info(
                "Payment webhook processed: booking_id=%s status=%s",
                booking.pk,
                payment_status,
            )

            return Response(
                {
                    "message": "Payment successful.",
                    "booking_id": booking.pk,
                    "payment_id": payment.pk,
                    "booking_status": booking.status,
                },
                status=status.HTTP_200_OK
            )

        if payment_status == "FAILED":
            payment, _ = Payment.objects.update_or_create(
                booking=booking,
                defaults={
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "status": Payment.Status.FAILED,
                },
            )

            booking.status = Booking.Status.PAYMENT_FAILED
            booking.save(update_fields=["status"])

            return Response(
                {
                    "message": "Payment failed.",
                    "booking_id": booking.pk,
                    "payment_id": payment.pk,
                    "booking_status": booking.status,
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {"error": "Unsupported payment status."},
            status=status.HTTP_400_BAD_REQUEST
        )