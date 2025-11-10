from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart, name='cart'),
    path('add/', views.cart_add, name='cart_add'),
    path('delete/', views.cart_delete, name='cart_delete'),  # ✅ FIXED

    path('update/', views.cart_update, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    path('admin/order/<int:order_id>/invoice/', views.admin_order_invoice, name='admin_order_invoice'),
    path('invoice/view/<int:order_id>/', views.view_invoice, name='view_invoice'),

    ]
