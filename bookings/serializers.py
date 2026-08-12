from rest_framework import serializers

from .models import Parent, LSAProfile, Booking, Payment


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = [
            "id",
            "name",
            "email",
            "created_at",
        ]


class LSAProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LSAProfile
        fields = [
            "id",
            "name",
            "email",
            "skills",
            "is_active",
            "created_at",
        ]


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id",
            "parent",
            "lsa",
            "start_time",
            "end_time",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
        ]

    def validate(self, attrs):
        start_time = attrs["start_time"]
        end_time = attrs["end_time"]
        lsa = attrs["lsa"]

        if end_time <= start_time:
            raise serializers.ValidationError(
            "End time must be after start time."
        )

        overlapping_booking = Booking.objects.filter(
            lsa=lsa,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exclude(
            status__in=[
                Booking.Status.CANCELLED,
                Booking.Status.PAYMENT_FAILED,
            ]
        )

        if overlapping_booking.exists():
            raise serializers.ValidationError(
            "The LSA is already booked during this time."
        )

        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "transaction_id",
            "amount",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
        ]