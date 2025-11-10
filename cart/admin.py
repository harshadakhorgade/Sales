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

# ---------------------------
# Order Admin
# ---------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount_paid', 'is_shipped', 'is_delivered', 'view_invoice_link')

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
