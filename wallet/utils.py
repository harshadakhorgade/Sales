# wallet/utils.py
from wallet.models import Wallet, WalletTransaction

def log_wallet_transaction(user, amount, description):
    """
    Records a credit transaction to user's wallet (for commission or others),
    assuming the amount is already added to wallet.balance elsewhere.
    """
    wallet, _ = Wallet.objects.get_or_create(user=user)

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type='credit',
        amount=amount,
        description=description
    )