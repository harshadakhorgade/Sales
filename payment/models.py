from django.db import models
from django.utils import timezone
from cart.models import Order
from users.models import CustomUser

class Payment(models.Model):
    PAYMENT_METHOD = (
        ('qr', 'QR (Offline)'),
        ('wallet', 'Wallet'),
        ('razorpay', 'Razorpay'),  # keep for legacy data if any
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='qr')

    # legacy Razorpay fields
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)

    # New / general fields
    transaction_id = models.CharField(max_length=100, blank=False, null=False)

    payment_proof = models.ImageField(upload_to='payment_screenshots/', null=True, blank=True)

    status = models.CharField(max_length=50, default='pending')  # e.g., pending, captured, failed
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Admin confirmation
    is_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.user.email} | {self.amount} | {self.payment_method}"

    def confirm(self):
        """Mark payment as confirmed and store timestamp"""
        self.is_confirmed = True
        self.confirmed_at = timezone.now()
        self.status = 'captured'
        self.save()
