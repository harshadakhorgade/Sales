from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from store.models import Product
from .serializers import CartSerializer



class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("== AddToCartView Called ==")
        print("User:", request.user)
        print("Authenticated:", request.user.is_authenticated)
        print("POST data:", request.data)

        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        cart, _ = Cart.objects.get_or_create(user=request.user)
        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        # Calculate total requested quantity
        total_quantity = cart_item.quantity + quantity if not created else quantity

        # Check stock
        if total_quantity > product.stock_quantity:
            return Response(
                {'error': f"Only {product.stock_quantity} item(s) available in stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save to cart
        if not created:
            cart_item.quantity = total_quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response({'message': 'Product added to cart'}, status=status.HTTP_200_OK)


class UpdateCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity'))

        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)

        product = cart_item.product

        # Stock check
        if quantity > product.stock_quantity:
            return Response(
                {'error': f"Only {product.stock_quantity} item(s) available in stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        return Response({'message': 'Cart updated'}, status=status.HTTP_200_OK)





class DeleteFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        cart_item.delete()

        return Response({'message': 'Product removed'}, status=status.HTTP_200_OK)

class CartTotalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        total = 0
        for item in cart.items.all():
            price = item.product.sale_price if item.product.is_sale else item.product.price
            total += price * item.quantity
        return Response({'total': total})
