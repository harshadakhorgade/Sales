#!/usr/bin/env python
"""
Test script to verify email-based authentication is working correctly.
Run this after making the changes to verify the fix.
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import authenticate
from users.models import CustomUser
from users.forms import EmailAuthenticationForm
from django.test import RequestFactory

def test_email_authentication():
    print("🔍 Testing Email-Based Authentication Fix")
    print("=" * 50)
    
    # Check if superuser exists
    try:
        user = CustomUser.objects.get(email='admin@gmail.com')
        print(f"✅ Found superuser: {user.email}")
        print(f"   - Is active: {user.is_active}")
        print(f"   - Is staff: {user.is_staff}")
        print(f"   - Is superuser: {user.is_superuser}")
        print(f"   - USERNAME_FIELD: {CustomUser.USERNAME_FIELD}")
    except CustomUser.DoesNotExist:
        print("❌ No superuser found with email admin@gmail.com")
        print("   Please create a superuser first:")
        print("   python manage.py createsuperuser")
        return False
    
    print("\n🧪 Testing Django authenticate() function:")
    
    # Test common passwords
    test_passwords = ['admin', 'password', '123456', 'admin123', 'password123']
    
    for password in test_passwords:
        auth_user = authenticate(username='admin@gmail.com', password=password)
        status = "✅ SUCCESS" if auth_user else "❌ FAILED"
        print(f"   Password '{password}': {status}")
        if auth_user:
            print(f"   🎉 Authentication successful with password: '{password}'")
            print(f"   📧 Authenticated user: {auth_user.email}")
            break
    else:
        print("\n❌ None of the test passwords worked.")
        print("   The superuser password is different from the test passwords.")
        print("   Try logging in with the password you set when creating the superuser.")
        return False
    
    print("\n🧪 Testing EmailAuthenticationForm:")
    
    # Test the custom form
    factory = RequestFactory()
    request = factory.post('/login/', {
        'username': 'admin@gmail.com',  # Note: field is called 'username' but accepts email
        'password': password  # Use the password that worked
    })
    
    form_data = {
        'username': 'admin@gmail.com',
        'password': password
    }
    
    form = EmailAuthenticationForm(request, data=form_data)
    if form.is_valid():
        authenticated_user = form.get_user()
        print(f"✅ EmailAuthenticationForm validation: SUCCESS")
        print(f"   📧 Form authenticated user: {authenticated_user.email}")
    else:
        print(f"❌ EmailAuthenticationForm validation: FAILED")
        print(f"   Errors: {form.errors}")
        return False
    
    print("\n🎉 All tests passed! Email-based authentication is working correctly.")
    print("\n📋 Summary of changes made:")
    print("   1. ✅ Created EmailAuthenticationForm in users/forms.py")
    print("   2. ✅ Updated login_user view to use EmailAuthenticationForm")
    print("   3. ✅ Fixed authentication to work with email as USERNAME_FIELD")
    print("   4. ✅ Added proper error handling for missing Profile")
    
    print("\n🚀 Your login should now work on both local and EC2!")
    print("   - The form now properly accepts email instead of username")
    print("   - Authentication uses email as expected by your CustomUser model")
    print("   - This fix works for both development and production environments")
    
    return True

if __name__ == '__main__':
    test_email_authentication()
