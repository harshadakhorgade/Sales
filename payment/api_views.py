# payment/api_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from decimal import Decimal

from cart.models import Cart, Order, OrderItem
from store.models import Product
from payment.models import Payment
from wallet.models import Wallet, WalletTransaction
from users.models import Profile
from mlmtree.utils import distribute_commission


class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

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
                # Create order
                order = Order.objects.create(
                    user=user,
                    full_name=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    amount_paid=order_total,
                    shipping_address="App - Not provided"
                )

                # Record payment
                Payment.objects.create(
                    user=user,
                    order=order,
                    status='captured',
                    amount=order_total,
                    payment_method='wallet'
                )

                # Deduct from wallet
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    amount=order_total,
                    description=f"Order #{order.id} paid via Wallet",
                    order=order
                )
                wallet.balance -= Decimal(order_total)
                wallet.save()

                # Create order items and update stock
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

                    # Distribute commission
                    for _ in range(quantity):
                        distribute_commission(user, product)

                    product.stock_quantity -= quantity
                    product.save()

                # Clear cart
                cart.items.all().delete()
                cart.delete()
                Profile.objects.filter(user=user).update(old_cart="")

            return Response({'success': True, 'order_id': order.id})

        except Exception as e:
            return Response({'error': str(e)}, status=500)
