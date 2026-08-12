from django.urls import path

from .views import BookingCreateView, LSASearchView, PaymentWebhookView


urlpatterns = [
    path(
        "bookings/",BookingCreateView.as_view(),name="booking-create",
    ),
    path(
        "lsas/search/",LSASearchView.as_view(),name="lsa-search",
    ),
    path("payments/webhook/",PaymentWebhookView.as_view(),name="payment-webhook",
),
]