from django.db import models
from store.models import Product
from users.models import CustomUser

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    shipping_address = models.TextField(max_length=15000)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='COD')
    payment_status = models.CharField(max_length=50, default='Pending')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('Pending', 'Pending'),
            ('Processing', 'Processing'),
            ('Shipped', 'Shipped'),
            ('Delivered', 'Delivered'),
            ('Cancelled', 'Cancelled'),
            ('Refunded', 'Refunded'),
        ],
        default='Pending'
    )
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    courier_service = models.CharField(max_length=100, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    is_shipped = models.BooleanField(default=False)
    shipped_at = models.DateTimeField(null=True, blank=True)
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id}"
    
    @property
    def is_payment_confirmed(self):
        # Check if any related payment is captured
        payment = getattr(self, 'payments', None)
        if payment:
            payment_obj = self.payments.first()  # assuming 1 payment per order
            if payment_obj and payment_obj.status == 'captured':
                return True
        return False

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"OrderItem {self.id} for Order {self.order.id}"


from django.db import models
from store.models import Product
from users.models import CustomUser

class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} for {self.user.email if self.user and self.user.email else 'Unknown'}"
    def get_prods(self):
        return self.items.select_related('product').all()
    def get_quants(self):
        return {str(item.product.id): item.quantity for item in self.items.all()}

    def order_total(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product and self.product.name else 'Unknown Product'}"

    @property
    def name(self):
        return self.product.name if self.product else ''

    @property
    def imageURL(self):
        if self.product and self.product.image:
            return self.product.image.url
        return ''

    @property
    def price(self):
        if hasattr(self.product, 'is_sale') and self.product.is_sale:
            return self.product.sale_price
        return self.product.price

    @property
    def is_sale(self):
        return hasattr(self.product, 'is_sale') and self.product.is_sale

    @property
    def total_price(self):
        return self.price * self.quantity
    
    @property
    def imageURL(self):
        try:
            return self.product.image.url if self.product.image else ""
        except AttributeError:
            return ""  # fallback if product.image doesn't exist
