from decimal import Decimal
from users.models import CustomUser
from wallet.models import Wallet
from wallet.utils import log_wallet_transaction  # ✅ Import transaction logger

def distribute_commission(user, product):
    """
    Distributes commission from product.special_commission_amount:
    - Up to 10 uplines (parent_node)
    - 1 parent_sponsor
    - Remaining shares to company (superuser)
    Also logs each credit in WalletTransaction.
    """
    if not product.special_commission_amount:
        return

    total_commission = Decimal(product.special_commission_amount)
    share = total_commission / Decimal(12)
    company = CustomUser.objects.filter(is_superuser=True).first()

    uplines_paid = 0
    current = user.parent_node

    # 1️⃣ Pay 10 uplines
    while current and uplines_paid < 10:
        wallet, _ = Wallet.objects.get_or_create(user=current)
        wallet.balance += share
        wallet.save()
        log_wallet_transaction(
            user=current,
            amount=share,
            description=f"commission"
        )
        current = current.parent_node
        uplines_paid += 1

    # 2️⃣ Sponsor (if exists)
    sponsor_paid = False
    if user.parent_sponsor:
        sponsor = user.parent_sponsor
        wallet, _ = Wallet.objects.get_or_create(user=sponsor)
        wallet.balance += share
        wallet.save()
        log_wallet_transaction(
            user=sponsor,
            amount=share,
            description=f"Sponsor commission"
        )
        sponsor_paid = True

    # 3️⃣ Company gets remaining shares
    remaining_shares = (10 - uplines_paid) + (0 if sponsor_paid else 1) + 1
    if company:
        wallet, _ = Wallet.objects.get_or_create(user=company)
        wallet.balance += share * remaining_shares
        wallet.save()
        log_wallet_transaction(
            user=company,
            amount=share * remaining_shares,
            description=f"Company share of commission"
        )