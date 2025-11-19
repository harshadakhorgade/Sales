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

        upi_id = request.POST.get("upi_id")
        if not upi_id:
            return JsonResponse({"error": "UPI ID is required"}, status=400)

        request_id = request.POST.get('request_id') or str(uuid.uuid4())

        # Prevent duplicates
        if Payout.objects.filter(transaction_id=request_id).exists():
            messages.warning(request, "This withdrawal request already exists.")
            return redirect('wallet_transactions')

        with transaction.atomic():

            wallet = Wallet.objects.select_for_update().get(user=user)

            # Check available balance but DO NOT deduct here
            if wallet.balance < amount:
                return JsonResponse({"error": "Insufficient wallet balance."}, status=400)

            # Create payout request
            Payout.objects.create(
                user=user,
                upi_id=upi_id,
                amount=amount,
                status='pending',
                transaction_id=request_id
            )

        messages.success(
            request,
            f"Withdrawal request of ₹{amount} submitted successfully. Waiting for admin approval."
        )
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
