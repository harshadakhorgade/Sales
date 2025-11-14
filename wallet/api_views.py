from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from decimal import Decimal
from django.db import transaction
import uuid

from wallet.models import Wallet, WalletTransaction, Payout

# Serializer imports
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_from_wallet(request):
    user = request.user
    request_id = request.data.get("request_id") or str(uuid.uuid4())
    try:
        amount = Decimal(str(request.data.get("amount")))
        if amount <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return Response({"error": "Invalid amount"}, status=400)

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(user=user)
        if Payout.objects.filter(transaction_id=request_id).exists():
            return Response({"message": "Withdrawal already requested."}, status=200)
        if wallet.balance < amount:
            return Response({"error": "Insufficient balance."}, status=400)

        # Deduct from wallet
        wallet.balance -= amount
        wallet.save()

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type="debit",
            amount=amount,
            description=f"Payout request for ₹{amount}"
        )

        Payout.objects.create(
            user=user,
            amount=amount,
            status="Pending",
            transaction_id=request_id
        )

    return Response({"message": f"Withdrawal request of ₹{amount} submitted successfully."}, status=200)
