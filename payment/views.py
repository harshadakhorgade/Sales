from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from wallet.models import Wallet, WalletTransaction
from cart.models import Cart, Order, OrderItem
from store.models import Product
from users.models import ShippingAddress, Profile
from payment.models import Payment
from mlmtree.utils import distribute_commission


@csrf_exempt
def payment(request):
    """ Display payment page with cart and shipping info """
    try:
        cart_instance = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('store')

    cart_items = cart_instance.get_prods()
    cart_quantities = cart_instance.get_quants()
    total_quantity = sum(cart_quantities.values())
    order_total = cart_instance.order_total()

    try:
        shipping = ShippingAddress.objects.get(user=request.user)
    except ShippingAddress.DoesNotExist:
        messages.error(request, "Shipping address not found.")
        return redirect('store')

    request.session['shipping'] = {
        'email': shipping.email,
        'phone': shipping.phone,
        'shipping_address1': shipping.address1,
        'shipping_address2': shipping.address2,
        'city': shipping.city,
        'state': shipping.state,
        'zipcode': shipping.zipcode,
        'country': shipping.country
    }

    context = {
        'cart_items': cart_items,
        'order_total': order_total,
        'total_quantity': total_quantity,
        'shipping': request.session['shipping'],
        'currency': 'INR'
    }
    return render(request, 'payment/payment.html', context)


@csrf_exempt
def process_payment(request):
    """
    Handle the selection of payment method.
    - Wallet: redirect to wallet execution
    - QR: render QR code upload page
    """
    if request.method != "POST":
        return redirect('payment')

    payment_method = request.POST.get('payment_method')
    if not payment_method:
        messages.error(request, "No payment method selected.")
        return redirect('payment')

    request.session['payment_method'] = payment_method

    if payment_method == 'wallet':
        return redirect('payment_execute')

    # For offline QR payment
    try:
        cart_instance = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "No active cart found.")
        return redirect('store')

    order_total = cart_instance.order_total()
    qr_image_path = 'images/payment_qr.jpeg'  # relative to static/
    context = {
        'amount': order_total,
        'qr_image_path': qr_image_path,
    }
    return render(request, 'payment/process_payment.html', context)


@csrf_exempt
def payment_execute(request):
    """
    Execute payment for Wallet or QR/offline method
    """
    payment_method = request.session.get('payment_method')
    if not payment_method:
        messages.error(request, 'No payment method found. Please try again.')
        return redirect('payment')

    user = request.user
    shipping = request.session.get('shipping')

    # ---------- WALLET ----------
    if payment_method == 'wallet' and request.method == 'GET':
        try:
            cart_instance = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            messages.error(request, "Cart not found.")
            return redirect('store')

        cart_items = cart_instance.get_prods()
        cart_quantities = cart_instance.get_quants()
        order_total = cart_instance.order_total()

        wallet, _ = Wallet.objects.get_or_create(user=user)
        if wallet.balance < order_total:
            messages.error(request, "Insufficient wallet balance.")
            return redirect('payment')

        # Create order and payment
        full_name = f"{user.first_name} {user.last_name}"
        shipping_address = (
            f"{shipping['phone']}\n"
            f"{shipping['shipping_address1']}\n"
            f"{shipping['shipping_address2']}\n"
            f"{shipping['city']}\n"
            f"{shipping['state']}\n"
            f"{shipping['zipcode']}\n"
            f"{shipping['country']}"
        )

        order = Order.objects.create(
            user=user,
            full_name=full_name,
            email=user.email,
            amount_paid=order_total,
            shipping_address=shipping_address,
            payment_method='wallet',
            payment_status='Paid',
            transaction_id=''  # optional
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
            description=f"Order {order.id} placed with Wallet",
            order=order
        )

        wallet.balance -= order_total
        wallet.save()

        # Save order items, update stock, distribute commission
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

        # Clear cart
        cart_instance.items.all().delete()
        cart_instance.delete()
        Profile.objects.filter(user=user).update(old_cart="")
        request.session.pop('payment_method', None)

        messages.success(request, 'Payment successful via Wallet!')
        return redirect('order_success')


    # ---------- QR / OFFLINE ----------
    if payment_method == 'qr' and request.method == 'POST':
        payment_proof = request.FILES.get('payment_proof')
        transaction_id = request.POST.get('transaction_id', '').strip()

        try:
            cart_instance = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            messages.error(request, "No active cart found.")
            return redirect('store')

        cart_items = cart_instance.get_prods()
        cart_quantities = cart_instance.get_quants()
        order_total = cart_instance.order_total()

        full_name = f"{user.first_name} {user.last_name}"
        shipping_address = (
            f"{shipping['phone']}\n"
            f"{shipping['shipping_address1']}\n"
            f"{shipping['shipping_address2']}\n"
            f"{shipping['city']}\n"
            f"{shipping['state']}\n"
            f"{shipping['zipcode']}\n"
            f"{shipping['country']}"
        )

        # Create order with Pending payment
        order = Order.objects.create(
            user=user,
            full_name=full_name,
            email=user.email,
            amount_paid=order_total,
            shipping_address=shipping_address,
            payment_method='qr',
            payment_status='Pending',
            transaction_id=transaction_id if transaction_id else None
        )

        payment = Payment.objects.create(
            user=user,
            order=order,
            status='pending',
            amount=order_total,
            payment_method='qr',
            transaction_id=transaction_id if transaction_id else ''
        )

        if payment_proof:
            payment.payment_proof = payment_proof
            payment.save()

        # Save order items and update stock (commission deferred)
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
            product.stock_quantity -= quantity
            product.save()

        # Clear cart
        cart_instance.items.all().delete()
        cart_instance.delete()
        Profile.objects.filter(user=user).update(old_cart="")
        request.session.pop('payment_method', None)

        messages.success(request, 'Payment proof submitted. Your order is pending verification.')
        return redirect('order_success')

    messages.error(request, 'Invalid or unsupported payment method selected.')
    return redirect('payment')



# utils or views
from cart.models import Order, OrderItem
from mlmtree.utils import distribute_commission

def confirm_qr_payment(order: Order):
    """Call this after admin verifies QR payment"""
    if order.payment_status == 'Paid':
        print(f"Order {order.id} already marked as Paid. Skipping.")
        return

    order.payment_status = 'Paid'
    order.save()

    # Update payment status
    payment = order.payment_set.first()
    if payment:
        payment.status = 'captured'
        payment.save()

    order_items = OrderItem.objects.filter(order=order)
    for item in order_items:
        for _ in range(item.quantity):
            distribute_commission(order.user, item.product)

    print(f"✅ Commissions distributed for order {order.id}")



# @csrf_exempt
# def payment_execute(request):
#     """
#     Execute payment for Wallet or QR/offline method
#     """
#     payment_method = request.session.get('payment_method')
#     if not payment_method:
#         messages.error(request, 'No payment method found. Please try again.')
#         return redirect('payment')

#     user = request.user
#     shipping = request.session.get('shipping')

#     # ---------- WALLET ----------
#     if payment_method == 'wallet' and request.method == 'GET':
#         try:
#             cart_instance = Cart.objects.get(user=user)
#         except Cart.DoesNotExist:
#             messages.error(request, "Cart not found.")
#             return redirect('store')

#         cart_items = cart_instance.get_prods()
#         cart_quantities = cart_instance.get_quants()
#         order_total = cart_instance.order_total()

#         wallet, _ = Wallet.objects.get_or_create(user=user)
#         if wallet.balance < order_total:
#             messages.error(request, "Insufficient wallet balance.")
#             return redirect('payment')

#         # Create order and payment
#         full_name = f"{user.first_name} {user.last_name}"
#         shipping_address = (
#             f"{shipping['phone']}\n"
#             f"{shipping['shipping_address1']}\n"
#             f"{shipping['shipping_address2']}\n"
#             f"{shipping['city']}\n"
#             f"{shipping['state']}\n"
#             f"{shipping['zipcode']}\n"
#             f"{shipping['country']}"
#         )

#         order = Order.objects.create(
#             user=user,
#             full_name=full_name,
#             email=user.email,
#             amount_paid=order_total,
#             shipping_address=shipping_address,
#             payment_method='wallet',
#             payment_status='Paid',
#             transaction_id=''  # optional
#         )

#         Payment.objects.create(
#             user=user,
#             order=order,
#             status='captured',
#             amount=order_total,
#             payment_method='wallet'
#         )

#         WalletTransaction.objects.create(
#             wallet=wallet,
#             transaction_type='debit',
#             amount=order_total,
#             description=f"Order {order.id} placed with Wallet",
#             order=order
#         )

#         wallet.balance -= order_total
#         wallet.save()

#         # Save order items and update stock
#         for item in cart_items:
#             product = item.product
#             quantity = cart_quantities.get(str(product.id), item.quantity)
#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 user=user,
#                 quantity=quantity,
#                 price=item.price
#             )
#             for _ in range(quantity):
#                 distribute_commission(user, product)
#             product.stock_quantity -= quantity
#             product.save()

#         # Clear cart
#         cart_instance.items.all().delete()
#         cart_instance.delete()
#         Profile.objects.filter(user=user).update(old_cart="")
#         request.session.pop('payment_method', None)

#         messages.success(request, 'Payment successful via Wallet!')
#         return redirect('order_success')

#     # ---------- QR / OFFLINE ----------
#     if payment_method == 'qr' and request.method == 'POST':
#         payment_proof = request.FILES.get('payment_proof')
#         transaction_id = request.POST.get('transaction_id', '').strip()

#         try:
#             cart_instance = Cart.objects.get(user=user)
#         except Cart.DoesNotExist:
#             messages.error(request, "No active cart found.")
#             return redirect('store')

#         cart_items = cart_instance.get_prods()
#         cart_quantities = cart_instance.get_quants()
#         order_total = cart_instance.order_total()

#         full_name = f"{user.first_name} {user.last_name}"
#         shipping_address = (
#             f"{shipping['phone']}\n"
#             f"{shipping['shipping_address1']}\n"
#             f"{shipping['shipping_address2']}\n"
#             f"{shipping['city']}\n"
#             f"{shipping['state']}\n"
#             f"{shipping['zipcode']}\n"
#             f"{shipping['country']}"
#         )

#         # Create order with pending payment
#         order = Order.objects.create(
#             user=user,
#             full_name=full_name,
#             email=user.email,
#             amount_paid=order_total,
#             shipping_address=shipping_address,
#             payment_method='qr',
#             payment_status='Pending',
#             transaction_id=transaction_id if transaction_id else None
#         )

#         payment = Payment.objects.create(
#             user=user,
#             order=order,
#             status='pending',
#             amount=order_total,
#             payment_method='qr',
#             transaction_id=transaction_id if transaction_id else ''
#         )

#         if payment_proof:
#             payment.payment_proof = payment_proof
#             payment.save()

#         # Save order items and update stock
#         for item in cart_items:
#             product = item.product
#             quantity = cart_quantities.get(str(product.id), item.quantity)
#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 user=user,
#                 quantity=quantity,
#                 price=item.price
#             )
#             for _ in range(quantity):
#                 distribute_commission(user, product)
#             product.stock_quantity -= quantity
#             product.save()

#         # Clear cart
#         cart_instance.items.all().delete()
#         cart_instance.delete()
#         Profile.objects.filter(user=user).update(old_cart="")
#         request.session.pop('payment_method', None)

#         messages.success(request, 'Payment proof submitted. Your order is pending verification.')
#         return redirect('order_success')

#     messages.error(request, 'Invalid or unsupported payment method selected.')
#     return redirect('payment')


def order_success(request):
    return render(request, 'payment/order_success.html')


def payment_cancel(request):
    messages.warning(request, 'Payment canceled.')
    return render(request, 'payment/payment_cancel.html')
