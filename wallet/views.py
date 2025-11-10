from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
import uuid
from decimal import Decimal

from wallet.models import Wallet, WalletTransaction, Payout
from users.models import BankingDetails
from users.utils.razorpay_x import initiate_payout


# dyanamic fee+tax 


@login_required
def wallet_transactions_view(request):
    user = request.user

    # Always get wallet
    try:
        wallet = Wallet.objects.get(user=user)
    except Wallet.DoesNotExist:
        return JsonResponse({"error": "Wallet not found."}, status=404)

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

        # ✅ Prevent duplicate withdrawal requests
        if Payout.objects.filter(transaction_id=request_id).exists():
            messages.warning(request, "This withdrawal request was already processed.")
            return redirect('wallet_transactions')

        # ✅ Atomic DB transaction
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=user)

            if wallet.balance < amount:
                return JsonResponse({"error": "Insufficient wallet balance."}, status=400)

            # ✅ Get banking details
            try:
                banking = BankingDetails.objects.get(user=user)
            except BankingDetails.DoesNotExist:
                return JsonResponse({"error": "Banking details not found."}, status=404)

            # ✅ Initiate payout (for requested amount)
            payout_response = initiate_payout(banking.razorpay_fund_account_id, float(amount))
            if not payout_response or 'id' not in payout_response:
                return JsonResponse({
                    "error": f"Failed to initiate payout. Response: {payout_response}"
                }, status=400)

            # ✅ Extract fees + tax from Razorpay response (in paise)
            fees_paise = payout_response.get("fees", 0)
            tax_paise = payout_response.get("tax", 0)

            fee = Decimal(fees_paise) / 100
            tax = Decimal(tax_paise) / 100
            total_deduction = amount + fee + tax

            # ✅ Ensure wallet has enough for fees too
            if wallet.balance < total_deduction:
                return JsonResponse({"error": "Insufficient wallet balance for fees."}, status=400)

            # ✅ Deduct total amount from wallet
            wallet.balance -= total_deduction
            wallet.save()

            # ✅ Record wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='debit',
                amount=total_deduction,
                description=f'Payout ₹{amount} + Fees ₹{fee} + Tax ₹{tax}'
            )

            # ✅ Save payout record
            Payout.objects.create(
                user=user,
                amount=amount,
                razorpay_payout_id=payout_response['id'],
                status=payout_response.get('status', 'initiated'),
                transaction_id=request_id
            )

        messages.success(request, f'Withdrawal of ₹{amount} initiated successfully. '
                                  f'Fees ₹{fee} + Tax ₹{tax} applied. '
                                  f'Total deducted: ₹{total_deduction}.')

        # ✅ Redirect to prevent duplicate form submission
        return redirect('wallet_transactions')

    # GET request - Get bank details
    try:
        bank_details = BankingDetails.objects.get(user=user)
    except BankingDetails.DoesNotExist:
        bank_details = None

    return render(request, 'wallet/wallet_transactions.html', {
        'wallet': wallet,
        'transactions': transactions,
        'payouts': payouts,
        'bank_details': bank_details,
        'request_id': str(uuid.uuid4()),  # unique per form load
    })



# hardcoding 2.36 rs for IMPS payout mode 
# @login_required
# def wallet_transactions_view(request):
#     user = request.user

#     # Always get wallet
#     try:
#         wallet = Wallet.objects.get(user=user)
#     except Wallet.DoesNotExist:
#         return JsonResponse({"error": "Wallet not found."}, status=404)

#     transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')
#     payouts = Payout.objects.filter(user=user).order_by('-created_at')

#     if request.method == 'POST':
#         try:
#             amount = Decimal(str(request.POST.get('amount')))
#             if amount <= 0:
#                 raise ValueError()
#         except (TypeError, ValueError):
#             return JsonResponse({"error": "Invalid amount"}, status=400)

#         # ✅ Hardcoded IMPS fee (can later make configurable)
#         imps_fee = Decimal("2.36")
#         total_deduction = amount + imps_fee

#         # ✅ Prevent duplicate submission: Check if a request_id already exists
#         request_id = request.POST.get('request_id')
#         if Payout.objects.filter(transaction_id=request_id).exists():
#             messages.warning(request, "This withdrawal request was already processed.")
#             return redirect('wallet_transactions')

#         # ✅ Atomic DB transaction to avoid race conditions
#         with transaction.atomic():
#             wallet = Wallet.objects.select_for_update().get(user=user)

#             if wallet.balance < total_deduction:
#                 return JsonResponse({"error": "Insufficient wallet balance."}, status=400)

#             # ✅ Get user's banking details
#             try:
#                 banking = BankingDetails.objects.get(user=user)
#             except BankingDetails.DoesNotExist:
#                 return JsonResponse({"error": "Banking details not found."}, status=404)

#             # ✅ Initiate payout (for only the requested amount)
#             payout_response = initiate_payout(banking.razorpay_fund_account_id, float(amount))

#             if not payout_response or 'id' not in payout_response:
#                 return JsonResponse({
#                     "error": f"Failed to initiate payout. Response: {payout_response}"
#                 }, status=400)

#             # ✅ Deduct from wallet (amount + fee)
#             wallet.balance -= total_deduction
#             wallet.save()

#             # ✅ Record wallet transaction
#             WalletTransaction.objects.create(
#                 wallet=wallet,
#                 transaction_type='debit',
#                 amount=total_deduction,
#                 description=f'Payout ₹{amount} + Fee ₹{imps_fee}'
#             )

#             # ✅ Save payout with unique request_id
#             Payout.objects.create(
#                 user=user,
#                 amount=amount,
#                 razorpay_payout_id=payout_response['id'],
#                 status=payout_response.get('status', 'initiated'),
#                 transaction_id=request_id or str(uuid.uuid4())  # unique ID
#             )

#         messages.success(request, f'Withdrawal of ₹{amount} initiated successfully. '
#                                   f'Fee of ₹{imps_fee} applied. Total deducted: ₹{total_deduction}.')

#         # ✅ Redirect to prevent double submission on refresh
#         return redirect('wallet_transactions')

#     # GET request
#     return render(request, 'wallet/wallet_transactions.html', {
#         'wallet': wallet,
#         'transactions': transactions,
#         'payouts': payouts,
#         'request_id': str(uuid.uuid4()),  # unique per form load
#     })




# without fee+tax

# @login_required
# def wallet_transactions_view(request):
#     user = request.user

#     # Always get wallet
#     try:
#         wallet = Wallet.objects.get(user=user)
#     except Wallet.DoesNotExist:
#         return JsonResponse({"error": "Wallet not found."}, status=404)

#     transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')
#     payouts = Payout.objects.filter(user=user).order_by('-created_at')

#     if request.method == 'POST':
#         try:
#             amount = Decimal(str(request.POST.get('amount')))
#             if amount <= 0:
#                 raise ValueError()
#         except (TypeError, ValueError):
#             return JsonResponse({"error": "Invalid amount"}, status=400)

#         # ✅ Prevent duplicate submission: Check if a request_id already exists
#         request_id = request.POST.get('request_id')
#         if Payout.objects.filter(transaction_id=request_id).exists():
#             messages.warning(request, "This withdrawal request was already processed.")
#             return redirect('wallet_transactions')

#         # ✅ Atomic DB transaction to avoid race conditions
#         with transaction.atomic():
#             wallet = Wallet.objects.select_for_update().get(user=user)

#             if wallet.balance < amount:
#                 return JsonResponse({"error": "Insufficient wallet balance."}, status=400)

#             # ✅ Get user's banking details
#             try:
#                 banking = BankingDetails.objects.get(user=user)
#             except BankingDetails.DoesNotExist:
#                 return JsonResponse({"error": "Banking details not found."}, status=404)

#             # ✅ Initiate payout
#             payout_response = initiate_payout(banking.razorpay_fund_account_id, float(amount))

#             if not payout_response or 'id' not in payout_response:
#                 return JsonResponse({
#                     "error": f"Failed to initiate payout. Response: {payout_response}"
#                 }, status=400)

#             # ✅ Deduct from wallet
#             wallet.balance -= amount
#             wallet.save()

#             # ✅ Record wallet transaction
#             WalletTransaction.objects.create(
#                 wallet=wallet,
#                 transaction_type='debit',
#                 amount=amount,
#                 description=f'Payout initiated: ₹{amount}'
#             )

#             # ✅ Save payout with unique request_id
#             Payout.objects.create(
#                 user=user,
#                 amount=amount,
#                 razorpay_payout_id=payout_response['id'],
#                 status=payout_response.get('status', 'initiated'),
#                 transaction_id=request_id or str(uuid.uuid4())  # unique ID
#             )

#         messages.success(request, f'Withdrawal of ₹{amount} initiated successfully.')

#         # ✅ Redirect to prevent double submission on refresh
#         return redirect('wallet_transactions')

#     # GET request
#     return render(request, 'wallet/wallet_transactions.html', {
#         'wallet': wallet,
#         'transactions': transactions,
#         'payouts': payouts,
#         'request_id': str(uuid.uuid4()),  # unique per form load
#     })



