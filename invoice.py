from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors


def create_invoice(
    bill_id,
    items,
    subtotal,
    gst_amount,
    cgst,
    sgst,
    grand_total,
    payment_method="CASH",
    payment_reference=""
):
    filename = f"invoice_{bill_id}.pdf"

    pdf = canvas.Canvas(filename, pagesize=A4)

    width, height = A4

    # =========================
    # HEADER
    # =========================

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(
        width / 2,
        height - 50,
        "SUPERMARKET INVOICE"
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        width / 2,
        height - 68,
        "Thank you for shopping with us!"
    )

    # =========================
    # BILL DETAILS
    # =========================

    y = height - 110

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, f"Bill ID: {bill_id}")

    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(
        width - 50,
        y,
        f"Payment: {payment_method}"
    )

    y -= 25

    if payment_reference:
        pdf.drawString(
            50,
            y,
            f"Payment Reference: {payment_reference}"
        )
        y -= 25

    # =========================
    # TABLE HEADER
    # =========================

    pdf.setStrokeColor(colors.black)

    pdf.line(50, y, width - 50, y)

    y -= 20

    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(50, y, "Product")
    pdf.drawString(250, y, "Qty")
    pdf.drawString(310, y, "Price")
    pdf.drawString(390, y, "GST")
    pdf.drawRightString(width - 50, y, "Total")

    y -= 10

    pdf.line(50, y, width - 50, y)

    y -= 20

    # =========================
    # ITEMS
    # =========================

    pdf.setFont("Helvetica", 10)

    for item in items:

        # Support dictionary format
        if isinstance(item, dict):

            product_name = item.get(
                "product_name",
                item.get("name", "")
            )

            quantity = item.get(
                "quantity",
                0
            )

            price = item.get(
                "price",
                item.get("selling_price", 0)
            )

            total = item.get(
                "total",
                0
            )

            gst_rate = item.get(
                "gst_rate",
                0
            )

        # Support tuple/list format
        else:

            product_name = item[0]
            quantity = item[1]
            price = item[2]
            total = item[3]

            if len(item) > 5:
                gst_rate = item[5]
            else:
                gst_rate = 0

        pdf.drawString(
            50,
            y,
            str(product_name)[:28]
        )

        pdf.drawString(
            250,
            y,
            str(quantity)
        )

        pdf.drawString(
            310,
            y,
            f"Rs. {float(price):.2f}"
        )

        pdf.drawString(
            390,
            y,
            f"{float(gst_rate):.1f}%"
        )

        pdf.drawRightString(
            width - 50,
            y,
            f"Rs. {float(total):.2f}"
        )

        y -= 20

        # New page if necessary
        if y < 100:

            pdf.showPage()

            pdf.setFont(
                "Helvetica",
                10
            )

            y = height - 50

    # =========================
    # TOTALS
    # =========================

    y -= 10

    pdf.line(
        300,
        y,
        width - 50,
        y
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        300,
        y,
        "Subtotal:"
    )

    pdf.drawRightString(
        width - 50,
        y,
        f"Rs. {float(subtotal):.2f}"
    )

    y -= 20

    pdf.drawString(
        300,
        y,
        "CGST:"
    )

    pdf.drawRightString(
        width - 50,
        y,
        f"Rs. {float(cgst):.2f}"
    )

    y -= 20

    pdf.drawString(
        300,
        y,
        "SGST:"
    )

    pdf.drawRightString(
        width - 50,
        y,
        f"Rs. {float(sgst):.2f}"
    )

    y -= 20

    pdf.drawString(
        300,
        y,
        "Total GST:"
    )

    pdf.drawRightString(
        width - 50,
        y,
        f"Rs. {float(gst_amount):.2f}"
    )

    y -= 30

    pdf.line(
        300,
        y,
        width - 50,
        y
    )

    y -= 25

    # =========================
    # GRAND TOTAL
    # =========================

    pdf.setFont(
        "Helvetica-Bold",
        14
    )

    pdf.drawString(
        300,
        y,
        "GRAND TOTAL:"
    )

    pdf.drawRightString(
        width - 50,
        y,
        f"Rs. {float(grand_total):.2f}"
    )

    # =========================
    # FOOTER
    # =========================

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawCentredString(
        width / 2,
        50,
        "Thank you for shopping with us!"
    )

    pdf.save()

    return filename


# =========================
# TEST
# =========================

if __name__ == "__main__":

    test_items = [
        {
            "product_name": "Maggi",
            "quantity": 2,
            "price": 14,
            "total": 28,
            "gst_rate": 5
        },
        {
            "product_name": "Milk",
            "quantity": 1,
            "price": 30,
            "total": 30,
            "gst_rate": 5
        }
    ]

    file = create_invoice(
        bill_id=1,
        items=test_items,
        subtotal=58,
        gst_amount=2.90,
        cgst=1.45,
        sgst=1.45,
        grand_total=60.90,
        payment_method="CASH",
        payment_reference=""
    )

    print(f"Invoice created: {file}")