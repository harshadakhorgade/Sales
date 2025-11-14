from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import BankingDetailsSerializer
from .models import BankingDetails

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_bank_details_api(request):
    # Prevent duplicate entries
    if BankingDetails.objects.filter(user=request.user).exists():
        return Response({"error": "Bank details already submitted"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = BankingDetailsSerializer(data=request.data)
    if serializer.is_valid():
        # Save bank details directly
        banking = BankingDetails(**serializer.validated_data)
        banking.user = request.user
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
