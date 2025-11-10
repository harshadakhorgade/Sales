from rest_framework import serializers
from store.models import Product
from .models import Cart, CartItem
from api.serializers import ProductSerializer

from django.contrib.auth import authenticate




# CartItem serializer with product and quantity
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']

# Full Cart with items
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at']
