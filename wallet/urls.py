from django.urls import path
from .views import wallet_transactions_view 

urlpatterns = [
    path('transactions/', wallet_transactions_view, name='wallet_transactions'),
]