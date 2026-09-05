from reportlab.pdfgen import canvas


def create_invoice(
    bill_id,
    product_name,
    quantity,
    price,
    total
):
    filename = f"invoice_{bill_id}.pdf"

    pdf = canvas.Canvas(filename)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(200, 800, "SUPERMARKET INVOICE")

    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, 750, f"Bill ID: {bill_id}")
    pdf.drawString(50, 730, f"Product: {product_name}")
    pdf.drawString(50, 710, f"Quantity: {quantity}")
    pdf.drawString(50, 690, f"Price: Rs. {price}")
    pdf.drawString(50, 670, f"Total: Rs. {total}")

    pdf.line(50, 650, 500, 650)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, 620, f"Grand Total: Rs. {total}")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        50,
        580,
        "Thank you for shopping with us!"
    )

    pdf.save()

    return filename


if __name__ == "__main__":

    file = create_invoice(
        1,
        "Maggi",
        2,
        14,
        28
    )

    print(f"Invoice created: {file}")