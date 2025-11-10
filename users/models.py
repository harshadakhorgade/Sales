from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from users.managers import CustomUserManager
from django.conf import settings
import random

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email', unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    unique_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    referral_code = models.CharField(max_length=100, blank=True, null=True)
    pan_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    parent_sponsor = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='sponsored_users'
    )
    parent_node = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='child_nodes'
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def generate_unique_id(self):
        company_name = "VGS"
        product_name = "SS"
        first_initial = self.first_name[0].upper() if self.first_name else 'X'
        last_initial = self.last_name[0].upper() if self.last_name else 'X'
        random_number = random.randint(1000000000, 9999999999)
        unique_id = f"{company_name}-{product_name}-{first_initial}{last_initial}-{random_number}"

        while CustomUser.objects.filter(unique_id=unique_id).exists():
            random_number = random.randint(1000000000, 9999999999)
            unique_id = f"{company_name}-{product_name}-{first_initial}{last_initial}-{random_number}"

        return unique_id

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        if not self.referral_code:
            self.referral_code = f"REF-{self.unique_id[-5:]}"
        super().save(*args, **kwargs)

    def get_referral_link(self):
        base_url = settings.FRONTEND_URL
        return f"{base_url}/users/register?ref={self.unique_id}"

    @property
    def referred_by(self):
        return self.parent_sponsor.email if self.parent_sponsor else "Company"

    @property
    def placed_under(self):
        return self.parent_node.email if self.parent_node else "Company"


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/profile_pic', null=True, blank=True, default='default/pic.png')
    date_modified = models.DateTimeField(auto_now=True)
    phone = models.CharField(max_length=20, blank=True)
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    zipcode = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    old_cart = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.user.email

    class Meta:
        verbose_name = 'User Profile'


class ShippingAddress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Shipping Addresses"

    def __str__(self):
        return f'Shipping Address - {str(self.id)}'

# users/models.py

from django.conf import settings  # Already imported
# REMOVE this line:
# from django.contrib.auth.models import User

class BankingDetails(models.Model):
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    account_holder_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    contact_type = models.CharField(max_length=20)
    razorpay_contact_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_fund_account_id = models.CharField(max_length=100, blank=True, null=True)




