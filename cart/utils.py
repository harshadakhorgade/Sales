from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from django.http import HttpResponse
from cart.models import Order

def generate_invoice(order_id):
    order = Order.objects.get(id=order_id)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Invoice #{order.id}")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Customer: {order.full_name or order.user.get_full_name()}")
    p.drawString(50, height - 100, f"Email: {order.email or order.user.email}")
    p.drawString(50, height - 120, f"Shipping Address: {order.shipping_address}")
    p.drawString(50, height - 140, f"Date: {order.date_ordered.strftime('%d %B %Y')}")

    # Table Header
    p.drawString(50, height - 180, "Product")
    p.drawString(250, height - 180, "Quantity")
    p.drawString(350, height - 180, "Price")
    p.drawString(450, height - 180, "Total")

    y = height - 200
    for item in order.items.all():
        p.drawString(50, y, item.product.name)
        p.drawString(250, y, str(item.quantity))
        p.drawString(350, y, f"{item.price}")
        p.drawString(450, y, f"{item.price * item.quantity}")
        y -= 20

    # Total
    p.drawString(50, y - 20, f"Total Amount Paid: ₹ {order.amount_paid}")
    
    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer
