from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order','payment_method','razorpay_order_id', 'razorpay_payment_id', 'status', 'amount', 'created_at')
    search_fields = ('razorpay_payment_id', 'razorpay_order_id', 'user__username')
