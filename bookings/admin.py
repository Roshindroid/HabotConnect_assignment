from django.contrib import admin

# Register your models here.

from .models import Parent, LSAProfile, Booking, Payment


admin.site.register(Parent)
admin.site.register(LSAProfile)
admin.site.register(Booking)
admin.site.register(Payment)