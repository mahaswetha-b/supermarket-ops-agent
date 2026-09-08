
import sqlite3
from datetime import datetime, timedelta
from pptx import Presentation
from pptx.util import Inches, Pt
import matplotlib.pyplot as plt
import os


DB_NAME = "supermarket.db"
OUTPUT_FILE = "weekly_sales_analysis.pptx"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


# =========================================================
# GET TABLE COLUMNS
# =========================================================

def get_columns(cursor, table_name):
    rows = cursor.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {row[1] for row in rows}


# =========================================================
# GET SALES DATA
# =========================================================

def get_sales_data():

    conn = get_connection()
    cursor = conn.cursor()

    bill_columns = get_columns(cursor, "bills")
    item_columns = get_columns(cursor, "bill_items")
    product_columns = get_columns(cursor, "products")

    # -----------------------------------------------------
    # TOTAL SALES
    # -----------------------------------------------------

    if "total" in bill_columns:

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM bills
        """)

    elif "grand_total" in bill_columns:

        cursor.execute("""
            SELECT COALESCE(SUM(grand_total), 0)
            FROM bills
        """)

    elif "total_amount" in bill_columns:

        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0)
            FROM bills
        """)

    elif "amount" in bill_columns:

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM bills
        """)

    else:

        cursor.execute("""
            SELECT 0
        """)

    total_sales = cursor.fetchone()[0] or 0


    # -----------------------------------------------------
    # TOTAL BILLS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM bills
    """)

    total_bills = cursor.fetchone()[0] or 0


    # -----------------------------------------------------
    # TOTAL GST
    # -----------------------------------------------------

    total_gst = 0

    if "gst_amount" in item_columns:

        cursor.execute("""
            SELECT COALESCE(SUM(gst_amount), 0)
            FROM bill_items
        """)

        total_gst = cursor.fetchone()[0] or 0

    elif "gst_amount" in bill_columns:

        cursor.execute("""
            SELECT COALESCE(SUM(gst_amount), 0)
            FROM bills
        """)

        total_gst = cursor.fetchone()[0] or 0


    # -----------------------------------------------------
    # PRODUCT SALES DATA
    # -----------------------------------------------------

    top_products = []


    # First try bill_items
    if (
        "product_name" in item_columns
        and "quantity" in item_columns
    ):

        total_column = None

        if "total" in item_columns:
            total_column = "total"

        elif "line_total" in item_columns:
            total_column = "line_total"

        elif "amount" in item_columns:
            total_column = "amount"


        if total_column:

            cursor.execute(f"""
                SELECT
                    product_name,
                    SUM(quantity),
                    SUM({total_column})
                FROM bill_items
                GROUP BY product_name
                ORDER BY SUM(quantity) DESC
                LIMIT 10
            """)

        else:

            cursor.execute("""
                SELECT
                    product_name,
                    SUM(quantity),
                    0
                FROM bill_items
                GROUP BY product_name
                ORDER BY SUM(quantity) DESC
                LIMIT 10
            """)

        top_products = cursor.fetchall()


    # -----------------------------------------------------
    # FALLBACK TO BILLS TABLE
    # -----------------------------------------------------

    # If bill_items has no data, use bills table.
    if not top_products:

        if (
            "product_name" in bill_columns
            and "quantity" in bill_columns
        ):

            if "total" in bill_columns:

                cursor.execute("""
                    SELECT
                        product_name,
                        SUM(quantity),
                        SUM(total)
                    FROM bills
                    GROUP BY product_name
                    ORDER BY SUM(quantity) DESC
                    LIMIT 10
                """)

            elif "grand_total" in bill_columns:

                cursor.execute("""
                    SELECT
                        product_name,
                        SUM(quantity),
                        SUM(grand_total)
                    FROM bills
                    GROUP BY product_name
                    ORDER BY SUM(quantity) DESC
                    LIMIT 10
                """)

            elif "total_amount" in bill_columns:

                cursor.execute("""
                    SELECT
                        product_name,
                        SUM(quantity),
                        SUM(total_amount)
                    FROM bills
                    GROUP BY product_name
                    ORDER BY SUM(quantity) DESC
                    LIMIT 10
                """)

            else:

                cursor.execute("""
                    SELECT
                        product_name,
                        SUM(quantity),
                        0
                    FROM bills
                    GROUP BY product_name
                    ORDER BY SUM(quantity) DESC
                    LIMIT 10
                """)

            top_products = cursor.fetchall()


    # -----------------------------------------------------
    # STOCK DATA
    # -----------------------------------------------------

    stock_data = []

    if (
        "name" in product_columns
        and "quantity" in product_columns
    ):

        cost_column = (
            "cost_price"
            if "cost_price" in product_columns
            else "0"
        )

        selling_column = (
            "selling_price"
            if "selling_price" in product_columns
            else "0"
        )

        cursor.execute(f"""
            SELECT
                name,
                quantity,
                {cost_column},
                {selling_column}
            FROM products
            ORDER BY quantity ASC
        """)

        stock_data = cursor.fetchall()


    conn.close()


    return (
        float(total_sales),
        int(total_bills),
        float(total_gst),
        top_products,
        stock_data
    )


# =========================================================
# CREATE SALES CHART
# =========================================================

def create_sales_chart(top_products):

    if not top_products:
        return None

    names = [
        str(row[0])
        for row in top_products[:5]
    ]

    quantities = [
        float(row[1])
        for row in top_products[:5]
    ]


    plt.figure(figsize=(8, 5))

    plt.bar(names, quantities)

    plt.title("Top Selling Products")

    plt.xlabel("Product")

    plt.ylabel("Quantity Sold")

    plt.xticks(
        rotation=30,
        ha="right"
    )

    plt.tight_layout()


    chart_file = "top_products_chart.png"

    plt.savefig(
        chart_file,
        dpi=150
    )

    plt.close()


    return chart_file


# =========================================================
# CREATE STOCK CHART
# =========================================================

def create_stock_chart(stock_data):

    if not stock_data:
        return None

    names = [
        str(row[0])
        for row in stock_data[:10]
    ]

    quantities = [
        float(row[1])
        for row in stock_data[:10]
    ]


    plt.figure(figsize=(8, 5))

    plt.bar(names, quantities)

    plt.title("Current Stock Levels")

    plt.xlabel("Product")

    plt.ylabel("Stock Quantity")

    plt.xticks(
        rotation=30,
        ha="right"
    )

    plt.tight_layout()


    chart_file = "stock_levels_chart.png"

    plt.savefig(
        chart_file,
        dpi=150
    )

    plt.close()


    return chart_file


# =========================================================
# ADD TITLE
# =========================================================

def add_title(
    slide,
    title,
    subtitle=None
):

    title_box = slide.shapes.title

    title_box.text = title

    title_box.text_frame.paragraphs[0].font.size = Pt(28)


    if subtitle:

        textbox = slide.shapes.add_textbox(
            Inches(1),
            Inches(1.1),
            Inches(10),
            Inches(0.6)
        )

        textbox.text_frame.text = subtitle

        textbox.text_frame.paragraphs[0].font.size = Pt(16)


# =========================================================
# CREATE WEEKLY REPORT
# =========================================================

def create_weekly_report():

    print("Reading supermarket database...")


    (
        total_sales,
        total_bills,
        total_gst,
        top_products,
        stock_data
    ) = get_sales_data()


    print("Database data loaded.")

    print(
        f"Top products found: {len(top_products)}"
    )

    print(
        f"Stock products found: {len(stock_data)}"
    )


    # -----------------------------------------------------
    # CREATE CHARTS
    # -----------------------------------------------------

    sales_chart = create_sales_chart(
        top_products
    )

    stock_chart = create_stock_chart(
        stock_data
    )


    # -----------------------------------------------------
    # CREATE POWERPOINT
    # -----------------------------------------------------

    prs = Presentation()


    # =====================================================
    # SLIDE 1 - TITLE
    # =====================================================

    slide = prs.slides.add_slide(
        prs.slide_layouts[0]
    )


    slide.shapes.title.text = (
        "Weekly Sales Analysis"
    )


    subtitle = slide.placeholders[1]


    subtitle.text = (
        "Supermarket Operations Management Agent\n"
        f"Generated on "
        f"{datetime.now().strftime('%d-%m-%Y')}"
    )


    # =====================================================
    # SLIDE 2 - SALES SUMMARY
    # =====================================================

    slide = prs.slides.add_slide(
        prs.slide_layouts[5]
    )


    add_title(
        slide,
        "Sales Summary",
        "Overall supermarket sales performance"
    )


    average_bill = (
        total_sales / total_bills
        if total_bills > 0
        else 0
    )


    textbox = slide.shapes.add_textbox(
        Inches(1),
        Inches(2),
        Inches(10),
        Inches(4)
    )


    text = (
        f"Total Sales: ₹{total_sales:,.2f}\n\n"
        f"Total Bills: {total_bills}\n\n"
        f"GST Collected: ₹{total_gst:,.2f}\n\n"
        f"Average Bill Value: "
        f"₹{average_bill:,.2f}"
    )


    textbox.text_frame.text = text


    for paragraph in textbox.text_frame.paragraphs:

        paragraph.font.size = Pt(22)


    # =====================================================
    # SLIDE 3 - TOP PRODUCTS
    # =====================================================

    slide = prs.slides.add_slide(
        prs.slide_layouts[5]
    )


    add_title(
        slide,
        "Top Selling Products",
        "Products with highest quantity sold"
    )


    if (
        sales_chart
        and os.path.exists(sales_chart)
    ):

        slide.shapes.add_picture(
            sales_chart,
            Inches(1),
            Inches(1.8),
            width=Inches(10)
        )


    else:

        textbox = slide.shapes.add_textbox(
            Inches(1),
            Inches(3),
            Inches(10),
            Inches(2)
        )

        textbox.text_frame.text = (
            "No sales data available."
        )


    # =====================================================
    # SLIDE 4 - PRODUCT SALES DETAILS
    # =====================================================

    slide = prs.slides.add_slide(
        prs.slide_layouts[5]
    )


    add_title(
        slide,
        "Product Sales Details",
        "Top selling products and revenue"
    )


    if top_products:

        rows = min(
            len(top_products),
            6
        ) + 1


        table = slide.shapes.add_table(
            rows,
            3,
            Inches(0.8),
            Inches(1.8),
            Inches(10.5),
            Inches(4.5)
        ).table


        table.cell(
            0,
            0
        ).text = "Product"


        table.cell(
            0,
            1
        ).text = "Qty Sold"


        table.cell(
            0,
            2
        ).text = "Sales"


        for i, row in enumerate(
            top_products[:6],
            start=1
        ):

            product_name = row[0]

            quantity = row[1]

            amount = row[2]


            table.cell(
                i,
                0
            ).text = str(product_name)


            table.cell(
                i,
                1
            ).text = f"{float(quantity):g}"


            table.cell(
                i,
                2
            ).text = (
                f"₹{float(amount):,.2f}"
            )


    else:

        textbox = slide.shapes.add_textbox(
            Inches(1),
            Inches(3),
            Inches(10),
            Inches(2)
        )

        textbox.text_frame.text = (
            "No product sales data available."
        )


    # =====================================================
    # SLIDE 5 - STOCK HEALTH
    # =====================================================

    slide = prs.slides.add_slide(
        prs.slide_layouts[5]
    )


    add_title(
        slide,
        "Stock Health",
        "Current inventory levels"
    )


    if (
        stock_chart
        and os.path.exists(stock_chart)
    ):

        slide.shapes.add_picture(
            stock_chart,
            Inches(1),
            Inches(1.8),
            width=Inches(10)
        )


    else:

        textbox = slide.shapes.add_textbox(
            Inches(1),
            Inches(3),
            Inches(10),
            Inches(2)
        )

        textbox.text_frame.text = (
            "No stock data available."
        )


    # =====================================================
    # SLIDE 6 - LOW STOCK ALERT
    # =====================================================

    slide = prs.slides.add_slide(
        prs.slide_layouts[5]
    )


    add_title(
        slide,
        "Low Stock Alert",
        "Products requiring attention"
    )


    low_stock = [
        row
        for row in stock_data
        if float(row[1]) <= 10
    ]


    textbox = slide.shapes.add_textbox(
        Inches(1),
        Inches(2),
        Inches(10),
        Inches(4)
    )


    if low_stock:

        text = (
            "⚠️ Products with stock ≤ 10:\n\n"
        )


        for product in low_stock:

            text += (
                f"• {product[0]} - "
                f"{float(product[1]):g} units\n"
            )


    else:

        text = (
            "✅ No low-stock products detected."
        )


    textbox.text_frame.text = text


    for paragraph in textbox.text_frame.paragraphs:

        paragraph.font.size = Pt(20)


    # =====================================================
    # SLIDE 7 - BUSINESS INSIGHTS
    # =====================================================

    slide = prs.slides.add_slide(
        prs.slide_layouts[5]
    )


    add_title(
        slide,
        "Business Insights",
        "Key observations from sales and inventory data"
    )


    textbox = slide.shapes.add_textbox(
        Inches(1),
        Inches(2),
        Inches(10),
        Inches(4.5)
    )


    insights = []


    if total_sales > 0:

        insights.append(
            f"• Total recorded sales are "
            f"₹{total_sales:,.2f}."
        )


    if total_bills > 0:

        insights.append(
            f"• {total_bills} bills have "
            f"been recorded."
        )


        insights.append(
            f"• Average bill value is "
            f"₹{average_bill:,.2f}."
        )


    if total_gst > 0:

        insights.append(
            f"• GST collected is "
            f"₹{total_gst:,.2f}."
        )


    if top_products:

        best_product = top_products[0][0]

        best_quantity = top_products[0][1]


        insights.append(
            f"• Best-selling product by "
            f"quantity: {best_product} "
            f"({float(best_quantity):g} units)."
        )


    if low_stock:

        insights.append(
            f"• {len(low_stock)} product(s) "
            f"are at or below the "
            f"low-stock threshold."
        )


    else:

        insights.append(
            "• No products are currently "
            "below the low-stock threshold."
        )


    if not insights:

        insights.append(
            "• No sufficient sales data "
            "is available for insights."
        )


    textbox.text_frame.text = (
        "\n\n".join(insights)
    )


    for paragraph in textbox.text_frame.paragraphs:

        paragraph.font.size = Pt(19)


    # =====================================================
    # SAVE POWERPOINT
    # =====================================================

    prs.save(
        OUTPUT_FILE
    )


    # -----------------------------------------------------
    # REMOVE TEMPORARY CHART FILES
    # -----------------------------------------------------

    if (
        sales_chart
        and os.path.exists(sales_chart)
    ):

        os.remove(sales_chart)


    if (
        stock_chart
        and os.path.exists(stock_chart)
    ):

        os.remove(stock_chart)


    print()

    print(
        "========================================"
    )

    print(
        "Weekly report created successfully!"
    )

    print(
        f"File: {OUTPUT_FILE}"
    )

    print(
        "========================================"
    )


    return OUTPUT_FILE


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    create_weekly_report()

