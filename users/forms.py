from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, AuthenticationForm
from django.contrib.auth import authenticate
from django import forms
from .models import CustomUser, Profile, ShippingAddress

from .models import BankingDetails


class EmailAuthenticationForm(AuthenticationForm):
    """Custom authentication form that uses email instead of username"""
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'placeholder': 'Enter your email',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': 'Enter your password',
            'class': 'form-control'
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')  # This is actually email
        password = self.cleaned_data.get('password')

        if username is not None and password:
            # Use email as username for authentication
            self.user_cache = authenticate(
                self.request,
                username=username,  # Django authenticate expects 'username' parameter
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class CustomUserCreationForm(UserCreationForm):
    """Form for Django admin user creation"""
    unique_id = forms.CharField(max_length=50, required=False, disabled=True, widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = CustomUser
        fields = ("email", "unique_id")


class CustomUserChangeForm(UserChangeForm):
    """Form for Django admin user updates"""
    unique_id = forms.CharField(max_length=50, required=False, disabled=True, widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = CustomUser
        fields = ("email", "unique_id")


class CustomUserRegistrationForm(UserCreationForm):
    """Form for user registration with additional required fields"""
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    pan_number = forms.CharField(
    max_length=10,
    required=True,
    widget=forms.TextInput(attrs={'placeholder': 'PAN Number'})
)


    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'pan_number', 'password1', 'password2')

    def clean_email(self):
        """Ensure the email is unique"""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_pan_number(self):
        """Ensure the PAN number is unique"""
        pan_number = self.cleaned_data.get('pan_number')
        if pan_number and CustomUser.objects.filter(pan_number=pan_number).exists():
            raise forms.ValidationError("A user with this PAN number already exists.")
        return pan_number


class UpdateUserForm(forms.ModelForm):
    """Form to update CustomUser + Profile image"""
    password = None  # Hide password field

    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    unique_id = forms.CharField(max_length=50, required=False, disabled=True, widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    
    # From Profile model
    image = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'unique_id']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class UpdateUserPassword(PasswordChangeForm):
    """Form for changing user password with improved placeholders"""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Current Password'}), 
        label="Current Password"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}), 
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password'}), 
        label="Confirm New Password"
    )


class UpdateInfoForm(forms.ModelForm):
    """Form for updating user profile information"""
    # Display user info as read-only fields
    full_name = forms.CharField(
        required=False, 
        disabled=True,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'placeholder': 'Full Name'})
    )
    email = forms.EmailField(
        required=False, 
        disabled=True,
        widget=forms.EmailInput(attrs={'readonly': 'readonly', 'placeholder': 'Email'})
    )
    
    # Editable profile fields
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Phone'}))
    address1 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Address 1'}))
    address2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Address 2'}))
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'City'}))
    state = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'State'}))
    zipcode = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Zip Code'}))
    country = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Country'}))

    class Meta:
        model = Profile
        fields = ["phone", "address1", "address2", "city", "state", "zipcode", "country"]

class ShippingAddressForm(forms.ModelForm):
    """Form for adding/updating a shipping address"""
    full_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Full Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Phone'}))
    address1 = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Address 1'}))
    address2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Address 2'}))
    city = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'City'}))
    state = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'State'}))
    zipcode = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Zip Code'}))
    country = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Country'}))

    class Meta:
        model = ShippingAddress
        fields = ["full_name", "email", "phone", "address1", "address2", "city", "state", "zipcode", "country"]




# users/forms.py

from django import forms


# forms.py
from django import forms
from .models import BankingDetails


class BankingDetailsForm(forms.ModelForm):
    account_holder_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter account holder name',
            'class': 'form-control'
        })
    )
    account_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter account number',
            'class': 'form-control'
        })
    )
    ifsc_code = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter IFSC code',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter email address',
            'class': 'form-control'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter phone number',
            'class': 'form-control'
        })
    )
    contact_type = forms.ChoiceField(
        choices=[('customer', 'Customer'), ('vendor', 'Vendor')],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = BankingDetails
        fields = ['account_holder_name', 'account_number', 'ifsc_code', 'email', 'phone_number', 'contact_type']

    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if account_number and not account_number.isdigit():
            raise forms.ValidationError("Account number should contain only digits.")
        return account_number

    def clean_ifsc_code(self):
        ifsc_code = self.cleaned_data.get('ifsc_code')
        if ifsc_code and len(ifsc_code) != 11:
            raise forms.ValidationError("IFSC code should be 11 characters long.")
        return ifsc_code.upper() if ifsc_code else ifsc_code
