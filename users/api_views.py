# users/api_views.py  

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import BankingDetailsSerializer
from .models import BankingDetails
from .utils.razorpay_x import create_contact, create_fund_account

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_bank_details_api(request):
    # 🚫 Prevent duplicate
    if BankingDetails.objects.filter(user=request.user).exists():
        return Response({"error": "Bank details already submitted"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = BankingDetailsSerializer(data=request.data)
    if serializer.is_valid():
        # Create instance but don’t save yet
        banking = BankingDetails(**serializer.validated_data)
        banking.user = request.user

        # 👉 Razorpay Contact
        contact = create_contact(
            name=banking.account_holder_name,
            email=banking.email,
            phone=banking.phone_number,
            contact_type=banking.contact_type
        )
        if not contact or 'id' not in contact:
            return Response({"error": "Failed to create contact in Razorpay"}, status=status.HTTP_400_BAD_REQUEST)
        banking.razorpay_contact_id = contact['id']

        # 👉 Razorpay Fund Account
        fund = create_fund_account(
            contact_id=banking.razorpay_contact_id,
            name=banking.account_holder_name,
            account_number=banking.account_number,
            ifsc=banking.ifsc_code
        )
        if not fund or 'id' not in fund:
            return Response({"error": "Failed to create fund account"}, status=status.HTTP_400_BAD_REQUEST)
        banking.razorpay_fund_account_id = fund['id']

        banking.save()
        return Response(BankingDetailsSerializer(banking).data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bank_details_api(request):
    try:
        bank_details = BankingDetails.objects.get(user=request.user)
        serializer = BankingDetailsSerializer(bank_details)
        return Response(serializer.data, status=200)
    except BankingDetails.DoesNotExist:
        return Response({"error": "Bank details not found"}, status=404)