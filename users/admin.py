from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, Profile, ShippingAddress ,BankingDetails 


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = ("id",
        "first_name", "last_name", "email", "unique_id", "get_parent_sponsor", "get_parent_node", 
        "is_staff", "is_active", "last_login", "date_joined"
    )
    list_filter = ("email", "is_staff", "is_active", "parent_sponsor")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "unique_id")}),
        ("Referral Details", {"fields": ("parent_sponsor", "parent_node")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )

    search_fields = ("email", "first_name", "last_name", "unique_id", "parent_sponsor__email", "parent_node__email")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions",)
    
    readonly_fields = ("id", "unique_id", "last_login", "date_joined",)

    def get_parent_sponsor(self, obj):
        return obj.parent_sponsor.email if obj.parent_sponsor else "Company"
    get_parent_sponsor.admin_order_field = 'parent_sponsor'
    get_parent_sponsor.short_description = 'Referred By'

    def get_parent_node(self, obj):
        return obj.parent_node.email if obj.parent_node else "Company"
    get_parent_node.admin_order_field = 'parent_node'
    get_parent_node.short_description = 'Placed Under'

    def save_model(self, request, obj, form, change):
        """Ensure unique_id is generated before saving"""
        if not obj.unique_id:
            obj.unique_id = obj.generate_unique_id()
        obj.save()


admin.site.register(CustomUser, CustomUserAdmin)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'get_unique_id', 'get_parent_node', 'phone', 'address1', 'city', 'state', 'zipcode', 'country', 'old_cart')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'user__parent_node__email')

    def get_unique_id(self, obj):
        return obj.user.unique_id
    get_unique_id.admin_order_field = 'user__unique_id'
    get_unique_id.short_description = 'Unique ID'

    def get_parent_node(self, obj):
        return obj.user.parent_node.email if obj.user.parent_node else "None"
    get_parent_node.admin_order_field = 'user__parent_node'
    get_parent_node.short_description = 'Parent Node'


admin.site.register(Profile, ProfileAdmin)


class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'full_name', 'email', 'address1', 'city', 'state', 'zipcode', 'country')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


admin.site.register(ShippingAddress, ShippingAddressAdmin)

@admin.register(BankingDetails)
class BankingDetailAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'account_holder_name', 
        'account_number', 
        'ifsc_code', 
        'email', 
        'phone_number', 
        'contact_type', 
        'razorpay_contact_id', 
        'razorpay_fund_account_id',
    ]
    search_fields = ['user__username', 'account_holder_name', 'email', 'phone_number']
    list_filter = ['contact_type']

