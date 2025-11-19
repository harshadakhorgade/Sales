from django.contrib import admin
from .models import Wallet, WalletTransaction, Payout

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__email',)

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'transaction_type', 'timestamp')
    search_fields = ('wallet__user__email',)
    list_filter = ('timestamp',)

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'created_at']
    search_fields = ['user__username']
    list_filter = ['status', 'created_at']

    def save_model(self, request, obj, form, change):
        """Deduct wallet only when admin marks payout as PAID."""

        old_status = None
        if obj.pk:
            old_status = Payout.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        # If admin changed status → PAID
        if old_status != "paid" and obj.status == "paid":
            wallet = obj.user.wallet

            if wallet.balance >= obj.amount:
                wallet.balance -= obj.amount
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    amount=obj.amount,
                    description=f"Payout approved by admin: ₹{obj.amount}"
                )
