from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from razorpay.errors import SignatureVerificationError
from wallet.models import Wallet, WalletTransaction
from cart.models import Cart, CartItem, Order, OrderItem
from store.models import Product
from users.models import ShippingAddress, Profile
from payment.models import Payment
from .razorpay import razorpay_client
from mlmtree.utils import distribute_commission

@csrf_exempt
def payment(request):
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
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'currency': 'INR'
    }
    return render(request, 'payment/payment.html', context)

@csrf_exempt
def process_payment(request):
    if request.method != "POST":
        return redirect('payment')

    payment_method = request.POST.get('payment_method')
    if not payment_method:
        messages.error(request, "No payment method selected.")
        return redirect('payment')

    request.session['payment_method'] = payment_method

    if payment_method == 'wallet':
        return redirect('payment_execute')

    try:
        cart_instance = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "No active cart found.")
        return redirect('store')

    order_total = cart_instance.order_total()
    data = {
        'amount': int(order_total * 100),
        'currency': 'INR',
        'payment_capture': 1
    }

    try:
        order = razorpay_client.order.create(data=data)
    except Exception as e:
        messages.error(request, f'Error creating Razorpay order: {str(e)}')
        return redirect('payment')

    request.session['razorpay_order_id'] = order['id']

    context = {
        'order_id': order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount_paise': order['amount'],
        'amount_rupees': order['amount'] / 100,
        'currency': order['currency'],
        'user': request.user
    }
    return render(request, 'payment/process_payment.html', context)

@csrf_exempt
def payment_execute(request):
    payment_method = request.session.get('payment_method')

    if not payment_method:
        messages.error(request, 'No payment method found. Please try again.')
        return redirect('payment')

    if payment_method == 'razorpay' and request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except SignatureVerificationError:
            messages.error(request, 'Payment verification failed. Please try again.')
            return redirect('payment')

        try:
            payment_data = razorpay_client.payment.fetch(payment_id)
            if payment_data['status'] == 'captured':
                cart_instance = Cart.objects.get(user=request.user)
                cart_items = cart_instance.get_prods()
                cart_quantities = cart_instance.get_quants()
                order_total = cart_instance.order_total()

                user = request.user
                shipping = request.session.get('shipping')
                amount_paid = order_total
                full_name = f"{user.first_name} {user.last_name}"
                email = user.email

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
                    email=email,
                    amount_paid=amount_paid,
                    shipping_address=shipping_address
                )

                Payment.objects.create(
                    user=user,
                    order=order,
                    razorpay_order_id=order_id,
                    razorpay_payment_id=payment_id,
                    status='captured',
                    amount=amount_paid,
                    payment_method='razorpay'
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

                cart_instance.items.all().delete()
                cart_instance.delete()
                Profile.objects.filter(user=user).update(old_cart="")
                request.session.pop('payment_method', None)

                messages.success(request, 'Payment successful!')
                return redirect('order_success')
            else:
                messages.error(request, 'Payment failed. Please try again.')
                return redirect('payment')

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('payment')

    elif payment_method == 'wallet' and request.method == 'GET':
        try:
            cart_instance = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            messages.error(request, "Cart not found.")
            return redirect('store')

        cart_items = cart_instance.get_prods()
        cart_quantities = cart_instance.get_quants()
        order_total = cart_instance.order_total()

        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        if wallet.balance < order_total:
            messages.error(request, "Insufficient wallet balance.")
            return redirect('payment')

        user = request.user
        shipping = request.session.get('shipping')
        amount_paid = order_total
        full_name = f"{user.first_name} {user.last_name}"
        email = user.email

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
            email=email,
            amount_paid=amount_paid,
            shipping_address=shipping_address
        )

        Payment.objects.create(
            user=user,
            order=order,
            status='captured',
            amount=amount_paid,
            payment_method='wallet'
        )

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='debit',
            amount=amount_paid,
            description=f"Order {order.id} placed with Wallet",
            order=order
        )

        wallet.balance -= amount_paid
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

        cart_instance.items.all().delete()
        cart_instance.delete()
        Profile.objects.filter(user=user).update(old_cart="")
        request.session.pop('payment_method', None)

        messages.success(request, 'Payment successful via Wallet!')
        return redirect('order_success')

    else:
        messages.error(request, 'Invalid payment method selected.')
        return redirect('payment')

def order_success(request):
    return render(request, 'payment/order_success.html')

def payment_cancel(request):
    messages.warning(request, 'Payment canceled.')
    return render(request, 'payment_cancel.html')