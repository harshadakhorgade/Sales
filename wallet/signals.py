# wallet/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser
from .models import Wallet

@receiver(post_save, sender=CustomUser)
def create_wallet_for_new_user(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'wallet'):
        Wallet.objects.create(user=instance)
