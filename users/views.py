from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .forms import (
    CustomUserRegistrationForm, UpdateUserForm, UpdateUserPassword,
    ShippingAddressForm, UpdateInfoForm, EmailAuthenticationForm, BankingDetailsForm
)
from .models import CustomUser, Profile, ShippingAddress, BankingDetails
from cart.models import Cart, CartItem, Order
from wallet.models import Wallet, WalletTransaction

import json


# ---------------------------
# ✅ USER REGISTRATION
# ---------------------------
def register_user(request):
    # Store referral ID if present
    if 'ref' in request.GET:
        request.session['referral_id'] = request.GET.get('ref')

    referral_id = request.session.get('referral_id')
    parent_sponsor = None
    if referral_id:
        try:
            parent_sponsor = CustomUser.objects.get(unique_id=referral_id)
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid referral link.")
            return redirect('register')

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.parent_sponsor = parent_sponsor
            user.save()

            request.session.pop('referral_id', None)
            login(request, user)
            messages.success(request, 'Registration successful. Please fill in your shipping info.')
            return redirect('update_info')
        else:
            messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = CustomUserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


# ---------------------------
# ✅ USER LOGIN / LOGOUT
# ---------------------------
def login_user(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Restore old cart if available
            try:
                current_user = Profile.objects.get(user=request.user)
                saved_cart = current_user.old_cart
                if saved_cart:
                    cart = Cart(request)
                    for key, value in json.loads(saved_cart).items():
                        cart.db_add(product=key, quantity=value)
            except Profile.DoesNotExist:
                pass

            messages.success(request, 'Login successful!')
            return redirect(request.GET.get('next', 'home'))
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})


def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out!')
    return redirect('home')


# ---------------------------
# ✅ UPDATE USER PROFILE
# ---------------------------
def update_user(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, request.FILES, instance=user)
        if user_form.is_valid():
            user_form.save()
            if 'image' in request.FILES:
                profile.image = request.FILES['image']
                profile.save()
            messages.success(request, 'User details updated.')
            return redirect('home')
    else:
        user_form = UpdateUserForm(instance=user, initial={'image': profile.image})

    return render(request, 'users/update_user.html', {'user_form': user_form})


# ---------------------------
# ✅ UPDATE SHIPPING / INFO
# ---------------------------
def update_info(request):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to update your info.")
        return redirect('login')

    profile, _ = Profile.objects.get_or_create(user=request.user)
    initial_data = {
        'full_name': f"{request.user.first_name} {request.user.last_name}".strip(),
        'email': request.user.email,
    }
    form = UpdateInfoForm(request.POST or None, instance=profile, initial=initial_data)

    if form.is_valid():
        form.save()
        messages.success(request, "Your profile info has been updated.")
        return redirect('home')

    return render(request, 'users/update_info.html', {'form': form})


# ---------------------------
# ✅ UPDATE PASSWORD
# ---------------------------
def update_password(request):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to update your password.")
        return redirect('home')

    if request.method == 'POST':
        form = UpdateUserPassword(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password updated successfully. Please log in again.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UpdateUserPassword(request.user)

    return render(request, 'users/update_password.html', {'form': form})


# ---------------------------
# ✅ USER PROFILE PAGE
# ---------------------------
@login_required
def user_profile(request):
    profile = Profile.objects.get(user=request.user)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')

    user_data = {
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'unique_id': request.user.unique_id,
        'referral_link': f"{request.scheme}://{request.get_host()}/users/register/?ref={request.user.unique_id}",
        'parent_sponsor': request.user.parent_sponsor.unique_id if request.user.parent_sponsor else "None",
        'profile_image': profile.image.url if profile.image else '/media/default/pic.png',
    }

    orders = Order.objects.filter(user=request.user).order_by('-date_ordered')

    return render(request, 'users/user_profile.html', {
        'user_data': user_data,
        'orders': orders,
        'wallet': wallet,
        'wallet_balance': wallet.balance,
        'transactions': transactions,
    })


# ---------------------------
# ✅ REFERRALS PAGE
# ---------------------------
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from wallet.models import WalletTransaction

@login_required
def my_referrals_view(request):
    referred_users = request.user.sponsored_users.all()

    # Calculate total earnings from commission transactions
    total_earnings = WalletTransaction.objects.filter(
        wallet__user=request.user,
        transaction_type='credit',
        description__icontains='commission'
    ).aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'referred_users': referred_users,
        'total_earnings': total_earnings,
    }

    return render(request, 'users/my_referrals.html', context)

# ---------------------------
# ✅ ADD BANK DETAILS (NO RAZORPAY)
# ---------------------------
@login_required
def add_bank_details(request):
    """User adds or views their bank details manually (no Razorpay API)."""
    banking = BankingDetails.objects.filter(user=request.user).first()

    if banking:
        return render(request, 'users/bank_details.html', {
            'banking_details': banking,
            'already_submitted': True
        })

    if request.method == 'POST':
        form = BankingDetailsForm(request.POST)
        if form.is_valid():
            banking = form.save(commit=False)
            banking.user = request.user
            banking.save()
            messages.success(request, "✅ Bank details submitted successfully.")
            return redirect('bank_details')
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = BankingDetailsForm()

    return render(request, 'users/bank_details.html', {
        'form': form,
        'already_submitted': False,
        'banking_details': banking
    })
