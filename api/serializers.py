from rest_framework import serializers
from store.models import Category, Product , ProductImage, MobileBanner
from users.models import Profile, ShippingAddress, CustomUser
from cart.models import Order, OrderItem


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'unique_id', 'referral_code', 'referred_by']
        ref_name = "ApiCustomUserSerializer"

class ProfileSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(source='user.referral_code', read_only=True)
    unique_id = serializers.CharField(source='user.unique_id', read_only=True)
    
    class Meta:
        model = Profile
        fields = '__all__'       
        
    def create(self, validated_data):
        user = self.context['request'].user
        profile, created = Profile.objects.update_or_create(user=user, defaults=validated_data)
        return profile

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
    
class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'       
        
    def create(self, validated_data):
        user = self.context['request'].user
        shipping_address, created = ShippingAddress.objects.update_or_create(user=user, defaults=validated_data)
        return shipping_address

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    product_images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'



class MobileBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileBanner
        fields = '__all__'
        
        

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'

# serializers.py

class ReferredUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'date_joined']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
