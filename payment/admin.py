from django.contrib import admin
from django.utils.html import format_html
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'order',
        'payment_method',
        'status',
        'amount',
        'transaction_id',
        'payment_proof_preview',
        'created_at',
    )
    search_fields = ('transaction_id', 'user__email', 'razorpay_payment_id', 'razorpay_order_id')
    readonly_fields = ('created_at', 'payment_proof_preview')
    list_filter = ('status', 'payment_method', 'created_at')
    actions = ['confirm_payment']

    def payment_proof_preview(self, obj):
        """Display uploaded payment proof as thumbnail."""
        if obj.payment_proof:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height:100px;"/></a>',
                obj.payment_proof.url,
                obj.payment_proof.url
            )
        return "-"
    payment_proof_preview.short_description = "Payment Proof"

    @admin.action(description='Confirm selected payments')
    def confirm_payment(self, request, queryset):
        """
        Mark pending payments as captured,
        update related orders as 'Paid',
        and distribute commissions automatically.
        """
        from mlmtree.utils import distribute_commission
        from cart.models import OrderItem

        updated = 0
        for payment in queryset.filter(status='pending'):
            payment.status = 'captured'
            payment.save()

            order = payment.order
            order.payment_status = 'Paid'
            order.save()

            # Distribute commissions for all products in this order
            order_items = OrderItem.objects.filter(order=order)
            for item in order_items:
                for _ in range(item.quantity):
                    distribute_commission(order.user, item.product)

            updated += 1

        self.message_user(
            request,
            f"{updated} payment(s) marked as confirmed and commissions distributed successfully."
        )











# from django.contrib import admin
# from django.utils.html import format_html
# from .models import Payment

# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 
#         'user', 
#         'order', 
#         'payment_method', 
#         'status', 
#         'amount', 
#         'transaction_id', 
#         'payment_proof_preview',  # show screenshot thumbnail
#         'created_at'
#     )
#     search_fields = ('transaction_id', 'user__email', 'razorpay_payment_id', 'razorpay_order_id')
#     readonly_fields = ('created_at', 'payment_proof_preview')
#     list_filter = ('status', 'payment_method', 'created_at')
#     actions = ['confirm_payment']

#     def payment_proof_preview(self, obj):
#         """ Display uploaded payment proof as thumbnail """
#         if obj.payment_proof:
#             return format_html(
#                 '<a href="{}" target="_blank"><img src="{}" style="max-height:100px;"/></a>',
#                 obj.payment_proof.url,
#                 obj.payment_proof.url
#             )
#         return "-"
#     payment_proof_preview.short_description = "Payment Proof"

#     @admin.action(description='Confirm selected payments')
#     def confirm_payment(self, request, queryset):
#         """ Mark pending payments as captured """
#         updated = queryset.filter(status='pending').update(status='captured')
#         self.message_user(request, f"{updated} payment(s) marked as confirmed.")
