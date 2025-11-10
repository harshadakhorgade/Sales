from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

from payment import razorpay
from .forms import (
    CustomUserRegistrationForm, UpdateUserForm, UpdateUserPassword, 
     ShippingAddressForm, UpdateInfoForm, EmailAuthenticationForm
)
from .models import CustomUser, Profile, ShippingAddress
import json
from cart.models import Cart, CartItem
from cart.models import Order
from django.contrib.auth.decorators import login_required 
from wallet.models import Wallet, WalletTransaction


from django.conf import settings

# PAN verification function removed - now using unique constraint instead


# Register User with Referral System# Register User with Referral System
def register_user(request):
    # Check if referral ID is in GET request and store it in session
    if 'ref' in request.GET:
        referral_id = request.GET.get('ref')
        request.session['referral_id'] = referral_id  # Store in session
        print(f"Referral ID received and stored in session: {referral_id}")

    # Retrieve referral ID from session (if available)
    referral_id = request.session.get('referral_id')
    print(f"Referral ID used for registration: {referral_id}")  # Debugging

    parent_sponsor = None
    if referral_id:
        try:
            parent_sponsor = CustomUser.objects.get(unique_id=referral_id)
            print(f"Parent Sponsor Found: {parent_sponsor.email}")  # Debugging
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid referral link.")
            return redirect('register')

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.parent_sponsor = parent_sponsor  # Assign sponsor
            user.save()
            print(f"User {user.email} saved with Parent Sponsor: {user.parent_sponsor.email if user.parent_sponsor else 'None'}")  # Debugging
            
            # Clear the referral ID from session after use
            request.session.pop('referral_id', None)

            login(request, user)
            messages.success(request, 'Registration successful. Please fill in your shipping info.')
            return redirect('update_info')
        else:
            print(form.errors)  # 👈 Add this
            messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = CustomUserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})




# Login User
def login_user(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Get the authenticated user from the form
            user = form.get_user()
            login(request, user)

            # Restore previous cart
            try:
                current_user = Profile.objects.get(user=request.user)
                saved_cart = current_user.old_cart
                if saved_cart:
                    cart = Cart(request)
                    for key, value in json.loads(saved_cart).items():
                        cart.db_add(product=key, quantity=value)
            except Profile.DoesNotExist:
                # Handle case where profile doesn't exist yet
                pass

            messages.success(request, 'Login successful!')
            
            # Redirect to next page if provided, otherwise go to home
            next_page = request.GET.get('next', 'home')
            return redirect(next_page)
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

# Logout User
def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out!')
    return redirect('home')

def update_user(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, request.FILES, instance=user)
        if user_form.is_valid():
            user_form.save()

            # Save profile image if provided
            if 'image' in request.FILES:
                profile.image = request.FILES['image']
                profile.save()

            messages.success(request, 'User details updated.')
            return redirect('home')
    else:
        user_form = UpdateUserForm(instance=user, initial={'image': profile.image})

    return render(request, 'users/update_user.html', {'user_form': user_form})

# Update User Profile Info
def update_info(request):
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)
        
        # Pre-populate form with user data
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
    messages.error(request, "You must be logged in to update your info.")
    return redirect('login')

# Update User Password
def update_password(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = UpdateUserPassword(request.user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been updated. Log in with your new password.")
                return redirect('login')
            messages.error(request, "Please correct the errors below.")
        else:
            form = UpdateUserPassword(request.user)
        return render(request, 'users/update_password.html', {'form': form})
    messages.error(request, "You must be logged in to update your password.")
    return redirect('home')

# User Profile View
@login_required
def user_profile(request):
    if request.user.is_authenticated:
        # Get user profile
        profile = Profile.objects.get(user=request.user)
        
        # Get or create wallet
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        
        # Fetch wallet transactions if wallet exists
        transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp') if wallet else []
        
        # Build user data dictionary
        user_data = {
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'unique_id': request.user.unique_id,
            'referral_link': f"{request.scheme}://{request.get_host()}/users/register/?ref={request.user.unique_id}",
            'parent_sponsor': request.user.parent_sponsor.unique_id if request.user.parent_sponsor else "None",
            'profile_image': profile.image.url if profile.image else '/media/default/pic.png',
        }
        
        # Fetch user's orders
        orders = Order.objects.filter(user=request.user).order_by('-date_ordered')
        
        # Render the user profile page with all the data
        return render(request, 'users/user_profile.html', {
            'user_data': user_data,
            'orders': orders,
            'wallet': wallet,
            'wallet_balance': wallet.balance,
            'transactions': transactions,
        })

    # Redirect unauthenticated users with an error message
    messages.error(request, "You must be logged in to view your profile.")
    return redirect('login')

@login_required
def my_referrals_view(request):
    referred_users = request.user.sponsored_users.all()
    return render(request, 'users/my_referrals.html', {'referred_users': referred_users})


# users/views.py
from .models import BankingDetails


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect



from .forms import BankingDetailsForm
from razorpay.errors import BadRequestError


from django.conf import settings
from django.contrib import messages



# import razorpay
# import logging


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import BankingDetailsForm
from .models import BankingDetails
from .utils.razorpay_x import create_contact, create_fund_account, initiate_payout

from django.shortcuts import get_object_or_404

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .forms import BankingDetailsForm
from .models import BankingDetails
from users.utils.razorpay_x import create_contact, create_fund_account


from django.contrib import messages  # ✅ for success messages

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import BankingDetails
from .forms import BankingDetailsForm
from .utils.razorpay_x import create_contact, create_fund_account  # if these are in a helper file

@login_required
def add_bank_details(request):
    try:
        banking = BankingDetails.objects.get(user=request.user)
        already_submitted = True
    except BankingDetails.DoesNotExist:
        banking = None
        already_submitted = False

    # ⛔ Do not allow re-submission if already exists
    if already_submitted:
        return render(request, 'users/bank_details.html', {
            'banking_details': banking,
            'already_submitted': True
        })

    if request.method == 'POST':
        form = BankingDetailsForm(request.POST)
        if form.is_valid():
            banking = form.save(commit=False)
            banking.user = request.user

            # 👉 Create Razorpay Contact
            contact = create_contact(
                name=banking.account_holder_name,
                email=banking.email,
                phone=banking.phone_number,
                contact_type=banking.contact_type
            )
            if not contact or 'id' not in contact:
                messages.error(request, "❌ Failed to create contact in Razorpay.")
                return redirect('bank_details')  # replace with your correct URL name

            banking.razorpay_contact_id = contact['id']

            # 👉 Create Fund Account
            fund = create_fund_account(
                contact_id=banking.razorpay_contact_id,
                name=banking.account_holder_name,
                account_number=banking.account_number,
                ifsc=banking.ifsc_code
            )
            if not fund or 'id' not in fund:
                messages.error(request, "❌ Failed to create fund account.")
                return redirect('bank_details')

            banking.razorpay_fund_account_id = fund['id']
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


