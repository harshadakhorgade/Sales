#!/usr/bin/env python
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

def test_authentication():
    print("Testing authentication for superuser...")
    
    # Get the superuser
    try:
        user = CustomUser.objects.get(email='admin@gmail.com')
        print(f"Found user: {user.email}")
        print(f"Is active: {user.is_active}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")
        print(f"Password hash exists: {bool(user.password)}")
    except CustomUser.DoesNotExist:
        print("No superuser found with email admin@gmail.com")
        return
    
    # Test common passwords
    common_passwords = [
        'admin',
        'password', 
        '123456',
        'admin123',
        'password123',
        'django123',
        'superuser',
        'root',
        '12345678'
    ]
    
    print("\nTesting common passwords:")
    for password in common_passwords:
        auth_user = authenticate(username='admin@gmail.com', password=password)
        status = "SUCCESS" if auth_user else "FAILED"
        print(f"Password '{password}': {status}")
        if auth_user:
            print(f"Authentication successful with password: {password}")
            break
    else:
        print("\nNone of the common passwords worked.")
        print("You may need to reset the superuser password.")

if __name__ == '__main__':
    test_authentication()