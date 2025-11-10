from rest_framework import serializers

class RazorpayVerificationSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()

class RazorpayOrderResponseSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    amount = serializers.IntegerField()
    currency = serializers.CharField()
    razorpay_key_id = serializers.CharField()