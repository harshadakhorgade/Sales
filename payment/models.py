# payment/models.py

from django.db import models
from cart.models import Order
from users.models import CustomUser

class Payment(models.Model):
    PAYMENT_METHOD = (
        ('razorpay', 'Razorpay'),
        ('wallet', 'Wallet'),
        # Add more payment methods as needed
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD,default='Cash')  # e.g., 'razorpay', 'wallet'
    razorpay_order_id = models.CharField(max_length=255)
    razorpay_payment_id = models.CharField(max_length=255)
    status = models.CharField(max_length=50)  # e.g., captured, failed
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.user.email} | {self.amount} | {self.payment_method}"
