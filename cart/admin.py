from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Order, OrderItem, Cart, CartItem

# ---------------------------
# Cart Admin
# ---------------------------
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total_items')

    def total_items(self, obj):
        return obj.items.count()

# # ---------------------------
# # Order Admin
# # ---------------------------
# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'amount_paid', 'is_shipped', 'is_delivered', 'view_invoice_link')

#     def view_invoice_link(self, obj):
#         url = reverse('admin_order_invoice', args=[obj.id])
#         return format_html('<a href="{}" target="_blank">View Invoice</a>', url)

#     view_invoice_link.short_description = "Invoice"

# # ---------------------------
# # Register other models
# # ---------------------------
# admin.site.register(Cart, CartAdmin)
# admin.site.register(CartItem)
# admin.site.register(OrderItem)

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Order, OrderItem, Cart, CartItem
from mlmtree.utils import distribute_commission

# ---------------------------
# QR Payment Verification Action
# ---------------------------
@admin.action(description="Mark selected QR payments as verified and distribute commission")
def verify_qr_payments(modeladmin, request, queryset):
    for order in queryset:
        if order.payment_method != 'qr' or order.payment_status == 'Paid':
            continue

        # Mark order as paid
        order.payment_status = 'Paid'
        order.save()

        # Update related payment
        payment = order.payment_set.first()
        if payment:
            payment.status = 'captured'
            payment.save()

        # Distribute commission for each order item
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            for _ in range(item.quantity):
                distribute_commission(order.user, item.product)

    modeladmin.message_user(request, "✅ Selected QR payments verified and commissions distributed.")


# ---------------------------
# Order Admin
# ---------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount_paid', 'is_shipped', 'is_delivered', 'view_invoice_link', 'payment_method', 'payment_status')
    actions = [verify_qr_payments]  # <-- Add the action here

    def view_invoice_link(self, obj):
        url = reverse('admin_order_invoice', args=[obj.id])
        return format_html('<a href="{}" target="_blank">View Invoice</a>', url)

    view_invoice_link.short_description = "Invoice"


# ---------------------------
# Register other models
# ---------------------------
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
admin.site.register(OrderItem)

