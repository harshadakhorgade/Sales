from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from django.http import HttpResponse
from cart.models import Order

def generate_invoice(order_id):
    order = Order.objects.get(id=order_id)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- Company Header ---
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 50, "Skyage Global Pvt Ltd")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, "Invoice")
    p.line(50, height - 75, width - 50, height - 75)

    # --- Customer Details ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 100, f"Invoice #: {order.id}")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 120, f"Customer: {order.full_name or order.user.get_full_name()}")
    p.drawString(50, height - 140, f"Email: {order.email or order.user.email}")
    p.drawString(50, height - 160, f"Shipping Address: {order.shipping_address}")
    p.drawString(50, height - 180, f"Date: {order.date_ordered.strftime('%d %B %Y')}")

    # --- Table Header ---
    table_y = height - 210
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, table_y, "Product")
    p.drawString(250, table_y, "Quantity")
    p.drawString(350, table_y, "Price")
    p.drawString(450, table_y, "Total")
    p.line(50, table_y - 5, width - 50, table_y - 5)

    # --- Table Rows ---
    y = table_y - 25
    p.setFont("Helvetica", 12)
    for index, item in enumerate(order.items.all()):
        if index % 2 == 0:
            p.setFillColorRGB(0.95, 0.95, 0.95)  # light gray background
            p.rect(50, y - 5, width - 100, 20, fill=1, stroke=0)
            p.setFillColor(colors.black)
        p.drawString(50, y, item.product.name)
        p.drawString(250, y, str(item.quantity))
        p.drawString(350, y, f"₹{item.price:.2f}")
        p.drawString(450, y, f"₹{item.price * item.quantity:.2f}")
        y -= 25

    # --- Total Amount ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y - 10, f"Total Amount Paid: ₹{order.amount_paid:.2f}")
    p.line(50, y - 15, width - 50, y - 15)

    # --- Footer ---
    p.setFont("Helvetica", 10)
    p.drawString(50, 50, "Skyage Global Pvt Ltd")
    p.drawString(50, 35, "123, Business Street, City, Country")
    p.drawString(50, 20, "Email: info@skyageglobal.com | Phone: +91-XXXXXXXXXX")

    # Finish PDF
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
