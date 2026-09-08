from database import (
    get_stock,
    get_product_details,
    get_low_stock,
    get_sales_summary,
    add_product,
    receive_stock,
    sell_product
)

from customer_account import get_balance


def stock_tool(product_name):
    return str(get_stock(product_name))


def product_details_tool(product_name):
    return str(get_product_details(product_name))


def low_stock_tool():
    return str(get_low_stock())


def sales_summary_tool():
    return str(get_sales_summary())


def customer_balance_tool(customer_name):
    return str(get_balance(customer_name))


def add_product_tool(
    product_name,
    cost_price,
    selling_price,
    quantity,
    hsn_code="0000",
    gst_rate=0
):
    try:
        if cost_price <= 0:
            return "Error: Cost price must be greater than 0."

        if selling_price <= 0:
            return "Error: Selling price must be greater than 0."

        if quantity <= 0:
            return "Error: Quantity must be greater than 0."

        if selling_price < cost_price:
            return "Error: Selling price cannot be lower than cost price."

        add_product(
            product_name,
            cost_price,
            selling_price,
            quantity,
            hsn_code,
            gst_rate
        )

        return (
            f"Product added successfully.\n"
            f"Product: {product_name}\n"
            f"Quantity: {quantity}\n"
            f"Cost Price: ₹{cost_price:.2f}\n"
            f"Selling Price: ₹{selling_price:.2f}\n"
            f"HSN: {hsn_code}\n"
            f"GST: {gst_rate}%"
        )

    except Exception as e:
        return f"Error adding product: {e}"


def receive_stock_tool(
    product_name,
    quantity,
    cost_price,
    selling_price,
    hsn_code="0000",
    gst_rate=0
):
    try:
        if quantity <= 0:
            return "Error: Quantity must be greater than 0."

        if cost_price <= 0:
            return "Error: Cost price must be greater than 0."

        if selling_price <= 0:
            return "Error: Selling price must be greater than 0."

        if selling_price < cost_price:
            return "Error: Selling price cannot be lower than cost price."

        receive_stock(
            product_name,
            quantity,
            cost_price,
            selling_price,
            hsn_code,
            gst_rate
        )

        current_stock = get_stock(product_name)

        return (
            f"Stock received successfully.\n"
            f"Product: {product_name}\n"
            f"Quantity received: {quantity}\n"
            f"Cost Price: ₹{cost_price:.2f}\n"
            f"Selling Price: ₹{selling_price:.2f}\n"
            f"Current Stock: {current_stock}"
        )

    except Exception as e:
        return f"Error receiving stock: {e}"


# =========================
# SELL PRODUCT TOOL
# =========================

def sell_product_tool(
    product_name,
    quantity,
    payment_method="CASH",
    payment_reference=""
):
    try:
        if quantity <= 0:
            return "❌ Quantity must be greater than 0."

        payment_method = payment_method.upper()

        if payment_method not in ["CASH", "UPI", "CARD"]:
            return "❌ Payment method must be CASH, UPI, or CARD."

        result = sell_product(
            product_name=product_name,
            quantity=quantity,
            payment_method=payment_method,
            payment_reference=payment_reference
        )

        if isinstance(result, dict):

            return (
                f"✅ Sale completed successfully.\n\n"
                f"Product: {result.get('product_name', product_name)}\n"
                f"Quantity sold: {result.get('quantity', quantity)}\n"
                f"Total: ₹{result.get('grand_total', 0):.2f}\n"
                f"Payment: {payment_method}\n"
                f"Remaining Stock: {result.get('remaining_stock', 'Unknown')}"
            )

        return str(result)

    except Exception as e:

        error = str(e)

        if "Insufficient stock" in error:
            return f"❌ {error}"

        if "below cost" in error.lower():
            return f"❌ {error}"

        return f"❌ Sale failed: {error}"