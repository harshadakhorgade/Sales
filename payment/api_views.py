# payment/api_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
from razorpay.errors import SignatureVerificationError
from cart.models import Cart, Order, OrderItem
from store.models import Product
from payment.models import Payment
from wallet.models import Wallet, WalletTransaction
from users.models import Profile
from .razorpay import razorpay_client
from mlmtree.utils import distribute_commission
from decimal import Decimal

from .serializers import (
    RazorpayVerificationSerializer,
    RazorpayOrderResponseSerializer
)

class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def create_razorpay_order(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
            amount = int(cart.order_total() * 100)

            razorpay_order = razorpay_client.order.create({
                'amount': amount,
                'currency': 'INR',
                'payment_capture': 1
            })

            serializer = RazorpayOrderResponseSerializer({
                'razorpay_order_id': razorpay_order['id'],
                'amount': razorpay_order['amount'],
                'currency': razorpay_order['currency'],
                'razorpay_key_id': settings.RAZORPAY_KEY_ID
            })
            return Response(serializer.data, status=200)

        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found.'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def verify_razorpay_payment(self, request):
        user = request.user
        serializer = RazorpayVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payment_id = data['razorpay_payment_id']
        order_id = data['razorpay_order_id']
        signature = data['razorpay_signature']

        if Payment.objects.filter(razorpay_payment_id=payment_id).exists():
            return Response({'message': 'Payment already verified.'}, status=200)

        try:
            razorpay_client.utility.verify_payment_signature(data)
        except SignatureVerificationError:
            return Response({'error': 'Invalid payment signature.'}, status=400)

        try:
            payment_data = razorpay_client.payment.fetch(payment_id)
            if payment_data['status'] != 'captured':
                return Response({'error': 'Payment not captured yet.'}, status=400)

            with transaction.atomic():
                cart = Cart.objects.get(user=user)
                cart_items = cart.get_prods()
                cart_quantities = cart.get_quants()
                order_total = cart.order_total()

                order = Order.objects.create(
                    user=user,
                    full_name=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    amount_paid=order_total,
                    shipping_address="App - Not provided"
                )

                Payment.objects.create(
                    user=user,
                    order=order,
                    payment_method='razorpay',
                    amount=order_total,
                    razorpay_order_id=order_id,
                    razorpay_payment_id=payment_id,
                    status='captured'
                )

                for item in cart_items:
                    product = item.product
                    quantity = cart_quantities.get(str(product.id), item.quantity)

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        user=user,
                        quantity=quantity,
                        price=item.price
                    )

                    for _ in range(quantity):
                        distribute_commission(user, product)

                    product.stock_quantity -= quantity
                    product.save()

                cart.items.all().delete()
                cart.delete()
                Profile.objects.filter(user=user).update(old_cart="")

            return Response({'success': True, 'order_id': order.id})

        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def wallet_payment(self, request):
        user = request.user

        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found.'}, status=404)

        cart_items = cart.get_prods()
        cart_quantities = cart.get_quants()
        order_total = cart.order_total()

        wallet, _ = Wallet.objects.get_or_create(user=user)
        if wallet.balance < order_total:
            return Response({'error': 'Insufficient wallet balance.'}, status=400)

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    full_name=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    amount_paid=order_total,
                    shipping_address="App - Not provided"
                )

                Payment.objects.create(
                    user=user,
                    order=order,
                    status='captured',
                    amount=order_total,
                    payment_method='wallet'
                )

                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    amount=order_total,
                    description=f"Order #{order.id} paid via Wallet",
                    order=order
                )

                wallet.balance -= Decimal(order_total)
                wallet.save()

                for item in cart_items:
                    product = item.product
                    quantity = cart_quantities.get(str(product.id), item.quantity)

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        user=user,
                        quantity=quantity,
                        price=item.price
                    )

                    for _ in range(quantity):
                        distribute_commission(user, product)

                    product.stock_quantity -= quantity
                    product.save()

                cart.items.all().delete()
                cart.delete()
                Profile.objects.filter(user=user).update(old_cart="")

            return Response({'success': True, 'order_id': order.id})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
