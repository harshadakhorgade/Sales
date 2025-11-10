# users/utils/razorpay_x.py

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from razorpay import Client, errors
# ✅ Define variables BEFORE using them
RAZORPAYX_KEY_ID = settings.RAZORPAYX_KEY_ID
RAZORPAYX_KEY_SECRET = settings.RAZORPAYX_KEY_SECRET

# ✅ Now use them

razorpay_client = Client(auth=(settings.RAZORPAYX_KEY_ID, settings.RAZORPAYX_KEY_SECRET))

def create_contact(name, email, phone, contact_type):
    url = "https://api.razorpay.com/v1/contacts"
    data = {
        "name": name,
        "email": email,
        "contact": phone,
        "type": contact_type
    }

    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth(RAZORPAYX_KEY_ID, RAZORPAYX_KEY_SECRET),
            json=data,
            timeout=10  # optional, add timeout
        )
        response.raise_for_status()  # raises HTTPError for bad status
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        print("Response content:", getattr(response, 'text', 'No response'))
        return None
    



def create_fund_account(contact_id, name, account_number, ifsc):
    url = "https://api.razorpay.com/v1/fund_accounts"
    data = {
        "contact_id": contact_id,
        "account_type": "bank_account",
        "bank_account": {
            "name": name,
            "ifsc": ifsc,
            "account_number": account_number
        }
    }

    response = requests.post(
        url,
        auth=HTTPBasicAuth(RAZORPAYX_KEY_ID, RAZORPAYX_KEY_SECRET),
        json=data
    )
    print("Created fund account:", data)
    return response.json()


import requests
from requests.auth import HTTPBasicAuth

def initiate_payout(fund_account_id, amount, purpose="payout"):
    url = "https://api.razorpay.com/v1/payouts"
    data = {
        "account_number": "2323230012900444",  # RazorpayX virtual account
        "fund_account_id": fund_account_id,
        "amount": int(amount * 100),  # Razorpay requires paise
        "currency": "INR",
        "mode": "IMPS",
        "purpose": purpose,
        "queue_if_low_balance": True
    }

    print("Initiating payout to fund_account_id:", fund_account_id)
    print("Payload being sent:", data)

    response = requests.post(
        url,
        auth=HTTPBasicAuth(RAZORPAYX_KEY_ID, RAZORPAYX_KEY_SECRET),
        json=data
    )

    if response.status_code != 200:
        print("❌ Razorpay payout failed with status:", response.status_code)
        print("❌ Response content:", response.text)
        return None

    print("✅ Payout Success:", response.json())
    return response.json()
