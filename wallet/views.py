from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
import uuid
from decimal import Decimal

from wallet.models import Wallet, WalletTransaction, Payout
from users.models import BankingDetails


@login_required
def wallet_transactions_view(request):
    user = request.user

    # Ensure wallet exists
    wallet, _ = Wallet.objects.get_or_create(user=user)

    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')
    payouts = Payout.objects.filter(user=user).order_by('-created_at')

    if request.method == 'POST':
        try:
            amount = Decimal(str(request.POST.get('amount')))
            if amount <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid amount"}, status=400)

        request_id = request.POST.get('request_id') or str(uuid.uuid4())

        # Prevent duplicate requests
        if Payout.objects.filter(transaction_id=request_id).exists():
            messages.warning(request, "This withdrawal request was already processed.")
            return redirect('wallet_transactions')

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=user)

            if wallet.balance < amount:
                return JsonResponse({"error": "Insufficient wallet balance."}, status=400)

            # Deduct from wallet
            wallet.balance -= amount
            wallet.save()

            # Record wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='debit',
                amount=amount,
                description=f'Payout request initiated for ₹{amount}'
            )

            # Save payout request
            Payout.objects.create(
                user=user,
                amount=amount,
                status='Pending',  # Admin will later mark as "Completed"
                transaction_id=request_id
            )

        messages.success(request, f'Withdrawal request of ₹{amount} submitted successfully. '
                                  f'Please wait for admin approval.')

        return redirect('wallet_transactions')

    # GET request
    try:
        bank_details = BankingDetails.objects.get(user=user)
    except BankingDetails.DoesNotExist:
        bank_details = None

    return render(request, 'wallet/wallet_transactions.html', {
        'wallet': wallet,
        'transactions': transactions,
        'payouts': payouts,
        'bank_details': bank_details,
        'request_id': str(uuid.uuid4()),
    })
