from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import login
from django.utils.decorators import method_decorator
from functools import wraps
from cart.models import Cart, CartItem, Order, OrderItem
from store.models import Product
from users.forms import ShippingAddressForm
from users.models import ShippingAddress


def login_required_ajax(view_func):
    """
    Custom decorator that handles authentication for both regular and AJAX requests.
    For AJAX requests, returns a JSON response indicating login is required.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Authentication required',
                'login_required': True,
                'login_url': '/users/login/'
            }, status=401)
        
        # For regular requests, redirect to login
        return redirect('login')
    
    return _wrapped_view




@login_required_ajax
def cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').all()
    total_quantity = sum(item.quantity for item in items)
    order_total = sum((item.product.sale_price if item.product.is_sale else item.product.price) * item.quantity for item in items)

    context = {
        'cart_items': items,
        'total_quantity': total_quantity,
        'order_total': order_total,
    }
    return render(request, 'cart/cart.html', context)


@login_required_ajax
def cart_add(request):
    if request.POST.get('product_id'):
        product_id = int(request.POST.get('product_id'))
        quantity = int(request.POST.get('product_qty'))
        product = get_object_or_404(Product, id=product_id)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        available_stock = product.stock_quantity
        if not created:
            total_quantity = cart_item.quantity + quantity
            cart_item.quantity = min(total_quantity, available_stock)
        else:
            cart_item.quantity = min(quantity, available_stock)

        cart_item.save()

        messages.success(request, f"{product.name} added to cart.")
        cart_quantity = sum(item.quantity for item in cart.items.all())
        return JsonResponse({'qty': cart_quantity})





@login_required_ajax
def cart_update(request):
    if request.method == 'POST' and request.POST.get('action') == 'post':
        try:
            cart_item_id = int(request.POST.get('product_id'))
            new_quantity = int(request.POST.get('product_qty'))

            print("✅ cart_update view triggered")
            print("🛒 CartItem ID received:", cart_item_id)

            # Get cart item by ID
            cart = get_object_or_404(Cart, user=request.user)
            cart_item = get_object_or_404(CartItem, cart=cart, id=cart_item_id)
            product = cart_item.product

            # Update quantity within product stock
            cart_item.quantity = min(new_quantity, product.stock_quantity)
            cart_item.save()

            return JsonResponse({'qty': cart_item.quantity})
        except Exception as e:
            print("❌ Error in cart_update:", e)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required_ajax
def cart_delete(request):
    if request.POST.get('action') == 'post':
        cart_item_id = int(request.POST.get('product_id'))  # This is actually CartItem.id
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
        cart_item.delete()

        messages.info(request, f"{cart_item.product.name} removed from cart.")
        return JsonResponse({'product': cart_item_id})

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('product').all()
    total_quantity = sum(item.quantity for item in cart_items)
    order_total = sum(
        (item.product.sale_price if item.product.is_sale else item.product.price) * item.quantity
        for item in cart_items
    )

    try:
        shipping_address = ShippingAddress.objects.get(user=request.user)
    except ShippingAddress.DoesNotExist:
        # Pre-fill from Profile if no ShippingAddress exists yet AND SAVE it
        profile = request.user.profile
        shipping_address = ShippingAddress.objects.create(
            user=request.user,
            full_name=f"{request.user.first_name} {request.user.last_name}",
            email=request.user.email,
            phone=profile.phone,
            address1=profile.address1,
            address2=profile.address2,
            city=profile.city,
            state=profile.state,
            zipcode=profile.zipcode,
            country=profile.country
        )

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=shipping_address)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            request.session['shipping'] = request.POST
            messages.success(request, "Your shipping information has been updated.")
            return redirect('payment')  # or wherever you want
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ShippingAddressForm(instance=shipping_address)

    context = {
        'cart_items': cart_items,
        'total_quantity': total_quantity,
        'order_total': order_total,
        'form': form,
        'user_profile': request.user.profile,
    }
    return render(request, 'cart/checkout.html', context)




# from users.forms import ShippingAddressForm

# @login_required
# def checkout(request):
#     cart = get_object_or_404(Cart, user=request.user)
#     cart_items = cart.items.select_related('product').all()
#     total_quantity = sum(item.quantity for item in cart_items)
#     order_total = sum(
#         (item.product.sale_price if item.product.is_sale else item.product.price) * item.quantity
#         for item in cart_items
#     )

#     # Try to get existing shipping address
#     try:
#         shipping_address = ShippingAddress.objects.get(user=request.user)
#     except ShippingAddress.DoesNotExist:
#         profile = request.user.profile
#         shipping_address = ShippingAddress(
#             user=request.user,
#             full_name=f"{request.user.first_name} {request.user.last_name}",
#             email=request.user.email,
#             phone=profile.phone,
#             address1=profile.address1,
#             address2=profile.address2,
#             city=profile.city,
#             state=profile.state,
#             zipcode=profile.zipcode,
#             country=profile.country
#         )

#     # Bind the form to POST data if submitted, otherwise prefill with instance
#     form = ShippingAddressForm(request.POST or None, instance=shipping_address)

#     if request.method == "POST":
#         if form.is_valid():
#             form.save()
#             # Continue checkout process (payment, order creation, etc.)
#             return redirect('payment')  # or whatever comes next

#     return render(request, 'cart/checkout.html', {
#         'cart_items': cart_items,
#         'total_quantity': total_quantity,
#         'order_total': order_total,
#         'form': form
#     })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-date_ordered')
    return render(request, 'users/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'users/order_detail.html', {'order': order})


from django.http import HttpResponse
from .utils import generate_invoice

def view_invoice(request, order_id):
    order = Order.objects.get(id=order_id)
    if request.user != order.user:
        return HttpResponse("Unauthorized", status=401)

    pdf_file = generate_invoice(order_id)
    return HttpResponse(pdf_file, content_type='application/pdf')


from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Order

@staff_member_required
def admin_order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'cart/order_invoice.html', {'order': order})