from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

from database import get_all_bills, get_sales_summary


def create_sales_report():

    filename = "daily_sales_report.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    story = []

    # TITLE
    story.append(
        Paragraph(
            "Supermarket Daily Sales Report",
            title_style
        )
    )

    story.append(Spacer(1, 20))

    # SALES SUMMARY
    summary = get_sales_summary()

    total_bills = summary[0]
    items_sold = summary[1]
    total_sales = summary[2]

    summary_data = [
        ["Total Bills", "Items Sold", "Total Sales"],
        [
            str(total_bills),
            str(items_sold),
            f"Rs. {total_sales:.2f}"
        ]
    ]

    summary_table = Table(summary_data)

    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 8)
        ])
    )

    story.append(summary_table)

    story.append(Spacer(1, 25))

    # BILL HISTORY
    story.append(
        Paragraph(
            "Bill History",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 10))

    bills = get_all_bills()

    bill_data = [
        ["Bill ID", "Product", "Qty", "Price", "Total"]
    ]

    for bill in bills:

        bill_id, product_name, quantity, price, total = bill

        bill_data.append([
            str(bill_id),
            product_name,
            str(quantity),
            f"Rs. {price:.2f}",
            f"Rs. {total:.2f}"
        ])

    bill_table = Table(bill_data)

    bill_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(bill_table)

    # CREATE PDF
    doc.build(story)

    print(
        f"Sales report created: {filename}"
    )

    return filename


if __name__ == "__main__":

    create_sales_report()