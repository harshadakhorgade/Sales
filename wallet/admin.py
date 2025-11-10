from django.contrib import admin
from .models import Wallet, WalletTransaction ,Payout

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
    list_display = [
        'user', 
        'amount', 
        'status', 
        'transaction_id', 
        'created_at'
    ]
    search_fields = ['user__username', 'transaction_id']
    list_filter = ['status', 'created_at']
