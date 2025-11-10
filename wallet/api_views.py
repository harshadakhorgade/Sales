# wallet/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wallet, WalletTransaction
from .serializers import WalletSerializer, WalletTransactionSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    serializer = WalletSerializer(wallet)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_transactions(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')
    serializer = WalletTransactionSerializer(transactions, many=True)
    return Response(serializer.data)







from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from decimal import Decimal
import uuid

from wallet.models import Wallet, WalletTransaction, Payout
from users.models import BankingDetails
from users.utils.razorpay_x import initiate_payout


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_from_wallet(request):
    user = request.user

    # ✅ Require request_id from client for idempotency
    request_id = request.data.get("request_id")
    if not request_id:
        return Response({"error": "Missing request_id"}, status=400)

    # ✅ Validate amount
    try:
        amount = Decimal(str(request.data.get("amount")))
        if amount <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return Response({"error": "Invalid amount"}, status=400)

    with transaction.atomic():
        # ✅ Lock wallet for concurrent safety
        wallet = Wallet.objects.select_for_update().get(user=user)

        # ✅ Check if payout with this request_id already exists
        existing_payout = Payout.objects.filter(transaction_id=request_id).first()
        if existing_payout:
            # Return previous status without charging again
            return Response({
                "message": f"Withdrawal of ₹{existing_payout.amount} already processed.",
                "status": existing_payout.status
            }, status=200)

        if wallet.balance < amount:
            return Response({"error": "Insufficient wallet balance."}, status=400)

        try:
            banking = BankingDetails.objects.get(user=user)
        except BankingDetails.DoesNotExist:
            return Response({"error": "Banking details not found."}, status=404)

        payout_response = initiate_payout(banking.razorpay_fund_account_id, float(amount))
        if not payout_response or "id" not in payout_response:
            return Response({
                "error": f"Failed to initiate payout. Response: {payout_response}"
            }, status=400)

        # ✅ Deduct wallet balance
        wallet.balance -= amount
        wallet.save()

        # ✅ Save wallet transaction
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type="debit",
            amount=amount,
            description=f"Payout initiated: ₹{amount}"
        )

        # ✅ Save payout record
        Payout.objects.create(
            user=user,
            amount=amount,
            razorpay_payout_id=payout_response["id"],
            status=payout_response.get("status", "initiated"),
            transaction_id=request_id
        )

    return Response({"message": f"Withdrawal of ₹{amount} initiated successfully."}, status=200)
