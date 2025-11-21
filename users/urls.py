from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('register/<str:referral_code>/', views.register_user, name='register_with_referral'),  # Add this line
    path('login/', views.login_user, name='signin'),
    path('logout/', views.logout_user, name='signout'),
    path('user_profile/', views.user_profile, name='user_profile'),
    path('update_user/', views.update_user, name='update_user'),
    path('update_password/', views.update_password, name='update_password'),
    # path('billing_info/', views.billing_info, name='billing_info'),
    path('update-info/', views.update_info, name='update_info'),
    path('welcome-letter/', views.welcome_letter_view, name='welcome_letter'),


    # path('shipping_info/', views.shipping_info, name='shipping_info'),
    path('my-referrals/', views.my_referrals_view, name='my_referrals'),


    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),

# razorpay_x
    path('bank_details/', views.add_bank_details, name='bank_details'),
    # path('withdraw/', views.withdraw, name='withdraw'),

]
