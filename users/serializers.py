from rest_framework import serializers
from .models import CustomUser, Profile
from django.contrib.auth.password_validation import validate_password

# users/serializers.py

from .models import BankingDetails

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for retrieving user details"""
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'unique_id', 'referral_code', 'referred_by']
        ref_name = "UserCustomSerializer"


class CustomUserCreateSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'unique_id', 'referral_code')

    def validate_email(self, value):
        """
        Ensure the email is unique.
        """
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate(self, data):
        """
        Ensure that passwords match.
        """
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        
        referred_by = None
        if referral_code:
            referred_by = CustomUser.objects.filter(unique_id=referral_code).first()
            
        user = CustomUser.objects.create(**validated_data, parent_sponsor=referred_by)
        user.set_password(password)
        user.save()
        return user

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for the user profile"""
    user = CustomUserSerializer(read_only=True)  # Embed user details
    unique_id = serializers.CharField(source='user.unique_id', read_only=True)  # Include unique_id from CustomUser

    class Meta:
        model = Profile
        fields = ['user', 'image', 'phone', 'address1', 'address2', 'city', 'state', 'zipcode', 'country', 'old_cart', 'unique_id']





# users/serializers.py
from rest_framework import serializers
from .models import BankingDetails

class BankingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankingDetails
        fields = [
            'id',
            'account_holder_name',
            'email',
            'phone_number',
            'contact_type',
            'account_number',
            'ifsc_code',
            'razorpay_contact_id',
            'razorpay_fund_account_id',
        ]
        read_only_fields = ['razorpay_contact_id', 'razorpay_fund_account_id']
