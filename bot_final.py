import os
import sqlite3

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from database import (
    create_database,
    get_stock,
    get_product_details,
    add_product,
    receive_stock,
    sell_product,
    get_sales_summary,
    get_low_stock,
    create_bill,
    add_bill_item,
    get_bill_items,
    remove_bill_item,
    finalize_bill,
    get_daily_close,
    update_bill_payment,
    update_price,
    set_product_gst
)

from customer_account import (
    add_credit,
    make_payment,
    get_balance
)

from sales_report import create_sales_report
from invoice import create_invoice

from agent import run_agent, clear_conversation


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


# =========================================================
# ACTIVE BILLS
# =========================================================

# user_id -> bill_id
user_bills = {}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_product_row(product_name):

    conn = sqlite3.connect("supermarket.db")
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        """
        SELECT
            id,
            name,
            cost_price,
            selling_price,
            quantity,
            hsn_code,
            gst_rate
        FROM products
        WHERE LOWER(name) = LOWER(?)
        """,
        (product_name.strip(),)
    ).fetchone()

    conn.close()

    return row


def get_bill_row(bill_id):

    conn = sqlite3.connect("supermarket.db")
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        """
        SELECT *
        FROM bills
        WHERE id = ?
        """,
        (bill_id,)
    ).fetchone()

    conn.close()

    return row


def calculate_bill_display_totals(bill_id):

    conn = sqlite3.connect("supermarket.db")

    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(total), 0),
            COALESCE(SUM(gst_amount), 0)
        FROM bill_items
        WHERE bill_id = ?
        """,
        (bill_id,)
    ).fetchone()

    conn.close()

    subtotal = float(row[0] or 0)
    gst_amount = float(row[1] or 0)

    cgst = round(gst_amount / 2, 2)
    sgst = round(gst_amount - cgst, 2)

    grand_total = round(
        subtotal + gst_amount,
        2
    )

    return {
        "subtotal": subtotal,
        "gst_amount": gst_amount,
        "cgst": cgst,
        "sgst": sgst,
        "grand_total": grand_total
    }


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = """
🛒 Supermarket Ops Agent

Available Commands:

📦 STOCK

/stock <product>

/addproduct <name> <cost> <selling> <quantity> [HSN] [GST%]

/receive <name> <quantity> <cost> <selling> [HSN] [GST%]

/updateprice <product> <selling price>

/setgst <product> <HSN> <GST%>

/sell <product> <quantity>


🧾 BILLING

/bill

/additem <product> <quantity>

/viewbill

/removeitem <product>

/finalize [Cash/UPI/Card] [Reference]

Example:

/finalize Cash
/finalize UPI UPI12345
/finalize Card CARD789


👤 CUSTOMER

/credit <customer> <amount>

/payment <customer> <amount> [method]

/balance <customer>

/payments [customer]


📊 REPORTS

/sales

/dailyclose

/lowstock


🤖 AI AGENT

/ask <question>


🆕 NEW CHAT

/newchat
"""

    await update.message.reply_text(message)


# =========================================================
# STOCK
# =========================================================

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "❌ Please enter product name.\n\n"
            "Example:\n"
            "/stock Maggi"
        )

        return

    product_name = " ".join(context.args)

    row = get_product_row(product_name)

    if not row:

        await update.message.reply_text(
            f"❌ Product '{product_name}' not found."
        )

        return

    await update.message.reply_text(
        f"📦 Product: {row['name']}\n"
        f"📊 Stock: {row['quantity']}\n"
        f"💰 Cost Price: ₹{row['cost_price']:.2f}\n"
        f"🏷️ Selling Price: ₹{row['selling_price']:.2f}\n"
        f"🧾 HSN Code: {row['hsn_code']}\n"
        f"📈 GST Rate: {row['gst_rate']:g}%"
    )


# =========================================================
# ADD PRODUCT
# =========================================================

async def addproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 4:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Use:\n"
            "/addproduct <name> <cost> <selling> <quantity> [HSN] [GST%]\n\n"
            "Example:\n"
            "/addproduct Milk 25 30 50 0401 5"
        )

        return

    try:

        args = context.args

        hsn_code = "0000"
        gst_rate = 0.0

        if len(args) >= 6:

            gst_rate = float(args[-1])
            hsn_code = args[-2]

            quantity = int(args[-3])
            selling_price = float(args[-4])
            cost_price = float(args[-5])

            product_name = " ".join(args[:-5])

        else:

            quantity = int(args[-1])
            selling_price = float(args[-2])
            cost_price = float(args[-3])

            product_name = " ".join(args[:-3])

        if not product_name:
            raise ValueError

        if cost_price <= 0:
            raise ValueError

        if selling_price <= 0:
            raise ValueError

        if quantity <= 0:
            raise ValueError

        if selling_price < cost_price:

            await update.message.reply_text(
                "❌ Selling price cannot be lower than cost price."
            )

            return

        if gst_rate < 0 or gst_rate > 100:
            raise ValueError

        add_product(
            product_name,
            cost_price,
            selling_price,
            quantity,
            hsn_code,
            gst_rate
        )

        await update.message.reply_text(
            f"✅ Product added successfully.\n\n"
            f"📦 Product: {product_name}\n"
            f"📊 Quantity: {quantity}\n"
            f"💰 Cost Price: ₹{cost_price:.2f}\n"
            f"🏷️ Selling Price: ₹{selling_price:.2f}\n"
            f"🧾 HSN: {hsn_code}\n"
            f"📈 GST: {gst_rate:g}%"
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid values.\n\n"
            "Example:\n"
            "/addproduct Milk 25 30 50 0401 5"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Error: {str(e)}"
        )


# =========================================================
# RECEIVE STOCK
# =========================================================

async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 4:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Use:\n"
            "/receive <name> <quantity> <cost> <selling> [HSN] [GST%]\n\n"
            "Example:\n"
            "/receive Maggi 50 12 14 1905 5"
        )

        return

    try:

        args = context.args

        hsn_code = "0000"
        gst_rate = 0.0

        if len(args) >= 6:

            gst_rate = float(args[-1])
            hsn_code = args[-2]

            selling_price = float(args[-3])
            cost_price = float(args[-4])
            quantity = int(args[-5])

            product_name = " ".join(args[:-5])

        else:

            selling_price = float(args[-1])
            cost_price = float(args[-2])
            quantity = int(args[-3])

            product_name = " ".join(args[:-3])

        if not product_name:
            raise ValueError

        if quantity <= 0:
            raise ValueError

        if cost_price <= 0 or selling_price <= 0:
            raise ValueError

        if selling_price < cost_price:

            await update.message.reply_text(
                "❌ Selling price cannot be lower than cost price."
            )

            return

        if gst_rate < 0 or gst_rate > 100:
            raise ValueError

        receive_stock(
            product_name,
            quantity,
            cost_price,
            selling_price,
            hsn_code,
            gst_rate
        )

        row = get_product_row(product_name)

        current_stock = row["quantity"] if row else 0

        await update.message.reply_text(
            f"✅ Stock received successfully.\n\n"
            f"📦 Product: {product_name}\n"
            f"📥 Quantity Received: {quantity}\n"
            f"💰 Cost Price: ₹{cost_price:.2f}\n"
            f"🏷️ Selling Price: ₹{selling_price:.2f}\n"
            f"🧾 HSN: {hsn_code}\n"
            f"📈 GST: {gst_rate:g}%\n"
            f"📊 Current Stock: {current_stock}"
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid values.\n\n"
            "Example:\n"
            "/receive Maggi 50 12 14 1905 5"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Error: {str(e)}"
        )


# =========================================================
# UPDATE PRICE
# =========================================================

async def updateprice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Example:\n"
            "/updateprice Maggi 14"
        )

        return

    try:

        selling_price = float(context.args[-1])

        product_name = " ".join(
            context.args[:-1]
        )

        row = get_product_row(product_name)

        if not row:

            await update.message.reply_text(
                f"❌ Product '{product_name}' not found."
            )

            return

        if selling_price <= 0:
            raise ValueError

        if selling_price < row["cost_price"]:

            await update.message.reply_text(
                f"❌ Selling price cannot be lower than cost price.\n\n"
                f"💰 Cost Price: ₹{row['cost_price']:.2f}"
            )

            return

        update_price(
            product_name,
            selling_price
        )

        await update.message.reply_text(
            f"✅ Selling price updated.\n\n"
            f"📦 Product: {row['name']}\n"
            f"💰 Cost Price: ₹{row['cost_price']:.2f}\n"
            f"🏷️ Old Price: ₹{row['selling_price']:.2f}\n"
            f"🏷️ New Price: ₹{selling_price:.2f}"
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Please enter a valid selling price."
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Error: {str(e)}"
        )


# =========================================================
# SET GST
# =========================================================

async def setgst(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 3:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Example:\n"
            "/setgst Maggi 1905 5"
        )

        return

    try:

        gst = float(context.args[-1])
        hsn = context.args[-2]

        name = " ".join(
            context.args[:-2]
        )

        if not 0 <= gst <= 100:
            raise ValueError

        set_product_gst(
            name,
            hsn,
            gst
        )

        await update.message.reply_text(
            f"✅ Tax details updated.\n\n"
            f"📦 Product: {name}\n"
            f"🏷️ HSN: {hsn}\n"
            f"🧾 GST: {gst:g}%"
        )

    except ValueError:

        await update.message.reply_text(
            "❌ GST rate must be between 0 and 100."
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Error: {str(e)}"
        )


# =========================================================
# SELL SINGLE PRODUCT
# =========================================================

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Example:\n"
            "/sell Maggi 2"
        )

        return

    try:

        quantity = int(
            context.args[-1]
        )

        product_name = " ".join(
            context.args[:-1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Quantity must be a number."
        )

        return

    if quantity <= 0:

        await update.message.reply_text(
            "❌ Quantity must be greater than 0."
        )

        return

    row = get_product_row(product_name)

    if not row:

        await update.message.reply_text(
            f"❌ Product '{product_name}' not found."
        )

        return

    if quantity > row["quantity"]:

        await update.message.reply_text(
            f"❌ Not enough stock.\n"
            f"📦 Available: {row['quantity']}"
        )

        return

    if row["selling_price"] < row["cost_price"]:

        await update.message.reply_text(
            f"❌ Sale blocked.\n\n"
            f"💰 Cost Price: ₹{row['cost_price']:.2f}\n"
            f"🏷️ Selling Price: ₹{row['selling_price']:.2f}"
        )

        return

    transaction_id = (
        f"sell:"
        f"{update.effective_chat.id}:"
        f"{update.update_id}"
    )

    try:

        result = sell_product(
            product_name,
            quantity,
            transaction_id
        )

        subtotal = result["subtotal"]
        gst_amount = result["gst_amount"]
        grand_total = result["grand_total"]

        await update.message.reply_text(
            f"✅ Sale successful!\n\n"
            f"🧾 Bill ID: {result['bill_id']}\n"
            f"📦 Product: {result['product_name']}\n"
            f"🔢 Quantity: {quantity}\n"
            f"💰 Price: ₹{result['price']:.2f}\n"
            f"💵 Subtotal: ₹{subtotal:.2f}\n"
            f"🧾 GST: ₹{gst_amount:.2f}\n"
            f"💵 Total: ₹{grand_total:.2f}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Sale failed.\n\n"
            f"Reason: {str(e)}"
        )


# =========================================================
# START NEW BILL
# =========================================================

async def bill(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id in user_bills:

        await update.message.reply_text(
            "⚠️ You already have an active bill.\n\n"
            "Use /viewbill to see it.\n"
            "Use /finalize to complete it."
        )

        return

    try:

        bill_id = create_bill()

        user_bills[user_id] = bill_id

        await update.message.reply_text(
            f"🧾 New bill started!\n\n"
            f"Bill ID: {bill_id}\n\n"
            "Add products using:\n"
            "/additem <product> <quantity>\n\n"
            "Example:\n"
            "/additem Maggi 2\n"
            "/additem Milk 1\n\n"
            "Use /viewbill to see the bill.\n"
            "Use /removeitem <product> to edit it.\n"
            "Use /finalize Cash to complete it."
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Could not create bill.\n\n"
            f"Reason: {str(e)}"
        )


# =========================================================
# ADD ITEM
# =========================================================

async def additem(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_bills:

        await update.message.reply_text(
            "❌ No active bill.\n\n"
            "Start one using /bill"
        )

        return

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Example:\n"
            "/additem Maggi 2"
        )

        return

    try:

        quantity = int(
            context.args[-1]
        )

        product_name = " ".join(
            context.args[:-1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Quantity must be a number."
        )

        return

    if quantity <= 0:

        await update.message.reply_text(
            "❌ Quantity must be greater than 0."
        )

        return

    bill_id = user_bills[user_id]

    row = get_product_row(product_name)

    if not row:

        await update.message.reply_text(
            f"❌ Product '{product_name}' not found."
        )

        return

    if row["selling_price"] < row["cost_price"]:

        await update.message.reply_text(
            "❌ Item cannot be added.\n\n"
            "Selling price cannot be lower than cost price."
        )

        return

    existing_quantity = 0

    items = get_bill_items(bill_id)

    for item in items:

        if item["product_name"].lower() == row["name"].lower():

            existing_quantity += item["quantity"]

    if existing_quantity + quantity > row["quantity"]:

        await update.message.reply_text(
            f"❌ Not enough stock.\n\n"
            f"📦 Available: {row['quantity']}\n"
            f"🛒 Already in bill: {existing_quantity}\n"
            f"➕ Requested: {quantity}"
        )

        return

    try:

        add_bill_item(
            bill_id,
            row["name"],
            quantity
        )

        subtotal = round(
            row["selling_price"] * quantity,
            2
        )

        gst_amount = round(
            subtotal * row["gst_rate"] / 100,
            2
        )

        item_total = round(
            subtotal + gst_amount,
            2
        )

        await update.message.reply_text(
            f"✅ Item added to bill.\n\n"
            f"📦 Product: {row['name']}\n"
            f"🔢 Quantity: {quantity}\n"
            f"💰 Price: ₹{row['selling_price']:.2f}\n"
            f"🧾 HSN: {row['hsn_code']}\n"
            f"📈 GST: {row['gst_rate']:g}%\n"
            f"🧾 GST Amount: ₹{gst_amount:.2f}\n"
            f"💵 Item Total: ₹{item_total:.2f}\n\n"
            f"Use /viewbill to see the bill."
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Could not add item.\n\n"
            f"Reason: {str(e)}"
        )


# =========================================================
# VIEW BILL
# =========================================================

async def viewbill(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_bills:

        await update.message.reply_text(
            "❌ No active bill.\n\n"
            "Start using /bill"
        )

        return

    bill_id = user_bills[user_id]

    items = get_bill_items(bill_id)

    if not items:

        await update.message.reply_text(
            f"🧾 Bill #{bill_id} is empty.\n\n"
            "Use /additem <product> <quantity>"
        )

        return

    message = (
        f"🧾 CURRENT BILL #{bill_id}\n\n"
    )

    for index, item in enumerate(items, 1):

        product_name = item["product_name"]
        quantity = item["quantity"]
        price = item["price"]
        total = item["total"]
        hsn_code = item["hsn_code"]
        gst_rate = item["gst_rate"]
        gst_amount = item["gst_amount"]

        message += (
            f"{index}. {product_name}\n"
            f" Qty: {quantity}\n"
            f" Price: ₹{price:.2f}\n"
            f" HSN: {hsn_code}\n"
            f" GST: {gst_rate:g}%\n"
            f" Subtotal: ₹{total:.2f}\n"
            f" GST Amount: ₹{gst_amount:.2f}\n"
            f" Item Total: ₹{total + gst_amount:.2f}\n\n"
        )

    totals = calculate_bill_display_totals(
        bill_id
    )

    message += (
        "--------------------\n"
        f"💰 SUBTOTAL: ₹{totals['subtotal']:.2f}\n"
        f"🧾 TOTAL GST: ₹{totals['gst_amount']:.2f}\n"
        f" ├─ CGST: ₹{totals['cgst']:.2f}\n"
        f" └─ SGST: ₹{totals['sgst']:.2f}\n"
        f"💵 GRAND TOTAL: ₹{totals['grand_total']:.2f}"
    )

    await update.message.reply_text(message)


# =========================================================
# REMOVE ITEM
# =========================================================

async def removeitem(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_bills:

        await update.message.reply_text(
            "❌ No active bill."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "❌ Please enter product name.\n\n"
            "Example:\n"
            "/removeitem Maggi"
        )

        return

    product_name = " ".join(
        context.args
    )

    bill_id = user_bills[user_id]

    items = get_bill_items(bill_id)

    found = False

    for item in items:

        if item["product_name"].lower() == product_name.lower():

            found = True
            break

    if not found:

        await update.message.reply_text(
            f"❌ '{product_name}' is not in the current bill."
        )

        return

    try:

        remove_bill_item(
            bill_id,
            product_name
        )

        await update.message.reply_text(
            f"✅ Removed '{product_name}' from bill."
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Could not remove item.\n\n"
            f"Reason: {str(e)}"
        )


# =========================================================
# FINALIZE BILL + PDF INVOICE
# =========================================================

async def finalize(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_bills:

        await update.message.reply_text(
            "❌ No active bill."
        )

        return

    bill_id = user_bills[user_id]

    items = get_bill_items(bill_id)

    if not items:

        await update.message.reply_text(
            "❌ Cannot finalize an empty bill."
        )

        return

    # -----------------------------------------------------
    # PAYMENT
    # -----------------------------------------------------

    payment_method = "CASH"
    payment_reference = ""

    if context.args:

        method = context.args[0].upper()

        if method not in [
            "CASH",
            "UPI",
            "CARD"
        ]:

            await update.message.reply_text(
                "❌ Invalid payment method.\n\n"
                "Use:\n"
                "/finalize Cash\n"
                "/finalize UPI UPI12345\n"
                "/finalize Card CARD789"
            )

            return

        payment_method = method

        if len(context.args) >= 2:

            payment_reference = " ".join(
                context.args[1:]
            )

    # -----------------------------------------------------
    # CALCULATE TOTALS
    # -----------------------------------------------------

    totals = calculate_bill_display_totals(
        bill_id
    )

    # -----------------------------------------------------
    # ATOMIC FINALIZE
    # -----------------------------------------------------

    try:

        result = finalize_bill(
            bill_id,
            payment_method,
            payment_reference
        )

        subtotal = float(
            result.get(
                "subtotal",
                totals["subtotal"]
            )
        )

        total_gst = float(
            result.get(
                "total_gst",
                result.get(
                    "gst_amount",
                    totals["gst_amount"]
                )
            )
        )

        cgst = float(
            result.get(
                "cgst",
                totals["cgst"]
            )
        )

        sgst = float(
            result.get(
                "sgst",
                totals["sgst"]
            )
        )

        grand_total = float(
            result.get(
                "grand_total",
                totals["grand_total"]
            )
        )

        # -------------------------------------------------
        # SUCCESS MESSAGE
        # -------------------------------------------------

        message = (
            f"✅ BILL FINALIZED!\n\n"
            f"🧾 Bill ID: {bill_id}\n"
            f"💳 Payment: {payment_method}\n"
        )

        if payment_reference:

            message += (
                f"🔖 Reference: {payment_reference}\n"
            )

        message += "\n"

        for item in items:

            product_name = item["product_name"]
            quantity = item["quantity"]
            price = item["price"]
            total = item["total"]
            hsn_code = item["hsn_code"]
            gst_rate = item["gst_rate"]
            gst_amount = item["gst_amount"]

            message += (
                f"📦 {product_name} × {quantity}\n"
                f" HSN: {hsn_code}\n"
                f" GST: {gst_rate:g}%\n"
                f" Subtotal: ₹{total:.2f}\n"
                f" GST: ₹{gst_amount:.2f}\n"
                f" Total: ₹{total + gst_amount:.2f}\n\n"
            )

        message += (
            "--------------------\n"
            f"💰 SUBTOTAL: ₹{subtotal:.2f}\n"
            f"🧾 TOTAL GST: ₹{total_gst:.2f}\n"
            f" ├─ CGST: ₹{cgst:.2f}\n"
            f" └─ SGST: ₹{sgst:.2f}\n"
            f"💵 GRAND TOTAL: ₹{grand_total:.2f}\n\n"
            f"📦 Stock updated successfully."
        )

        await update.message.reply_text(
            message
        )

        # -------------------------------------------------
        # GENERATE PDF INVOICE
        # -------------------------------------------------

        try:

            invoice_file = create_invoice(
                bill_id=bill_id,
                items=items,
                subtotal=subtotal,
                gst_amount=total_gst,
                cgst=cgst,
                sgst=sgst,
                grand_total=grand_total,
                payment_method=payment_method,
                payment_reference=payment_reference
            )

            if invoice_file and os.path.exists(invoice_file):

                with open(
                    invoice_file,
                    "rb"
                ) as document:

                    await update.message.reply_document(
                        document=document,
                        caption=(
                            f"🧾 Invoice for Bill #{bill_id}\n"
                            f"💵 Grand Total: ₹{grand_total:.2f}"
                        )
                    )

            else:

                await update.message.reply_text(
                    "⚠️ Bill completed, but invoice PDF could not be created."
                )

        except Exception as invoice_error:

            await update.message.reply_text(
                f"⚠️ Bill completed successfully.\n"
                f"❌ Invoice generation failed: {invoice_error}"
            )

        # -------------------------------------------------
        # CLEAR ACTIVE BILL
        # -------------------------------------------------

        del user_bills[user_id]

    except Exception as e:

        await update.message.reply_text(
            f"❌ Bill could not be finalized.\n\n"
            f"Reason: {str(e)}\n\n"
            f"⚠️ No partial stock update was made."
        )


# =========================================================
# CREDIT
# =========================================================

async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Example:\n"
            "/credit Ramesh 500"
        )

        return

    try:

        amount = float(
            context.args[-1]
        )

        customer_name = " ".join(
            context.args[:-1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Amount must be a number."
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ Credit amount must be greater than 0."
        )

        return

    try:

        balance_value = add_credit(
            customer_name,
            amount
        )

        await update.message.reply_text(
            f"✅ Credit added.\n\n"
            f"👤 Customer: {customer_name}\n"
            f"💰 Credit: ₹{amount:.2f}\n"
            f"📊 Total Balance: ₹{balance_value:.2f}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Error: {str(e)}"
        )


# =========================================================
# PAYMENT
# =========================================================

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Use:\n"
            "/payment <customer> <amount> [method]\n\n"
            "Examples:\n"
            "/payment Ramesh 300\n"
            "/payment Ramesh 300 Cash\n"
            "/payment Ramesh 300 UPI\n"
            "/payment Ramesh 300 Card"
        )

        return

    try:

        if (
            len(context.args) >= 3
            and context.args[-1].lower()
            in ["cash", "upi", "card"]
        ):

            payment_method = (
                context.args[-1].upper()
            )

            amount = float(
                context.args[-2]
            )

            customer_name = " ".join(
                context.args[:-2]
            )

        else:

            payment_method = "CASH"

            amount = float(
                context.args[-1]
            )

            customer_name = " ".join(
                context.args[:-1]
            )

    except ValueError:

        await update.message.reply_text(
            "❌ Amount must be a number."
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ Payment amount must be greater than 0."
        )

        return

    try:

        remaining = make_payment(
            customer_name,
            amount,
            payment_method
        )

        if remaining is None:

            await update.message.reply_text(
                f"❌ Customer '{customer_name}' not found."
            )

            return

        await update.message.reply_text(
            f"✅ Payment recorded.\n\n"
            f"👤 Customer: {customer_name}\n"
            f"💰 Paid: ₹{amount:.2f}\n"
            f"💳 Payment Method: {payment_method}\n"
            f"📊 Remaining Balance: ₹{remaining:.2f}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Payment failed.\n\n"
            f"Reason: {str(e)}"
        )


# =========================================================
# PAYMENT HISTORY
# =========================================================

async def payments(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = sqlite3.connect(
        "supermarket.db"
    )

    cursor = conn.cursor()

    try:

        if context.args:

            customer_name = " ".join(
                context.args
            )

            cursor.execute(
                """
                SELECT
                    customer_name,
                    amount,
                    payment_method,
                    payment_date
                FROM payment_history
                WHERE LOWER(customer_name)=LOWER(?)
                ORDER BY id DESC
                """,
                (customer_name,)
            )

        else:

            cursor.execute(
                """
                SELECT
                    customer_name,
                    amount,
                    payment_method,
                    payment_date
                FROM payment_history
                ORDER BY id DESC
                """
            )

        records = cursor.fetchall()

    except sqlite3.OperationalError:

        conn.close()

        await update.message.reply_text(
            "❌ Payment history table not available."
        )

        return

    conn.close()

    if not records:

        await update.message.reply_text(
            "💳 No payment history found."
        )

        return

    message = "💳 PAYMENT HISTORY\n\n"

    total_paid = 0

    for index, record in enumerate(
        records,
        1
    ):

        name = record[0]
        amount = record[1]
        method = record[2]
        payment_date = record[3]

        total_paid += amount

        message += (
            f"{index}. 👤 {name}\n"
            f" 💰 Amount: ₹{amount:.2f}\n"
            f" 💳 Method: {method}\n"
            f" 🕒 Date: {payment_date}\n\n"
        )

    message += (
        "--------------------\n"
        f"💰 Total Paid: ₹{total_paid:.2f}"
    )

    await update.message.reply_text(
        message
    )


# =========================================================
# BALANCE
# =========================================================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "❌ Please enter customer name.\n\n"
            "Example:\n"
            "/balance Ramesh"
        )

        return

    customer_name = " ".join(
        context.args
    )

    try:

        result = get_balance(
            customer_name
        )

        if result is None:

            await update.message.reply_text(
                f"❌ Customer '{customer_name}' not found."
            )

            return

        await update.message.reply_text(
            f"👤 Customer: {customer_name}\n"
            f"💰 Outstanding Balance: ₹{result:.2f}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Error: {str(e)}"
        )


# =========================================================
# SALES
# =========================================================

async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        summary = get_sales_summary()

        await update.message.reply_text(
            f"📊 SALES SUMMARY\n\n"
            f"{summary}"
        )

        filename = create_sales_report()

        if filename and os.path.exists(filename):

            with open(
                filename,
                "rb"
            ) as document:

                await update.message.reply_document(
                    document=document,
                    caption="📊 Sales Report"
                )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Sales report error: {str(e)}"
        )


# =========================================================
# LOW STOCK
# =========================================================

async def lowstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        result = get_low_stock()

        await update.message.reply_text(
            f"📦 {result}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Error: {str(e)}"
        )


# =========================================================
# DAILY CLOSE
# =========================================================

async def dailyclose(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        daily = get_daily_close()

        await update.message.reply_text(
            f"📊 {daily}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Daily Close Error: {str(e)}"
        )


# =========================================================
# NEW CHAT
# =========================================================

async def newchat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # -----------------------------------------------------
    # CLEAR AGENT CONVERSATION
    # -----------------------------------------------------

    clear_conversation(user_id)

    # -----------------------------------------------------
    # CLEAR UNFINISHED DRAFT BILL
    # -----------------------------------------------------

    if user_id in user_bills:

        bill_id = user_bills[user_id]

        conn = sqlite3.connect(
            "supermarket.db"
        )

        try:

            conn.execute(
                """
                DELETE FROM bill_items
                WHERE bill_id = ?
                """,
                (bill_id,)
            )

            conn.execute(
                """
                DELETE FROM bills
                WHERE id = ?
                  AND bill_type = 'HEADER'
                """,
                (bill_id,)
            )

            conn.commit()

        finally:

            conn.close()

        del user_bills[user_id]

    await update.message.reply_text(
        "🆕 New chat started!\n\n"
        "Your previous conversation and draft bill have been cleared.\n\n"
        "✅ Products\n"
        "✅ Sales history\n"
        "✅ Customer balances\n"
        "are still safely preserved.\n\n"
        "You can start a new request."
    )


# =========================================================
# AI AGENT - /ask COMMAND
# =========================================================

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "❌ Please ask a question.\n\n"
            "Examples:\n"
            "/ask what is the stock of Maggi?\n"
            "/ask show me the balance of Ramesh\n"
            "/ask which products are low in stock?\n"
            "/ask show sales summary"
        )

        return

    question = " ".join(
        context.args
    )

    user_id = update.effective_user.id

    try:

        answer = run_agent(
            question,
            user_id
        )

        await update.message.reply_text(
            f"🤖 {answer}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Agent Error: {str(e)}"
        )


# =========================================================
# NORMAL TEXT - AI AGENT
# =========================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    if not text:
        return

    user_id = update.effective_user.id

    try:

        answer = run_agent(
            text,
            user_id
        )

        await update.message.reply_text(
            f"🤖 {answer}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Agent Error: {str(e)}"
        )


# =========================================================
# MAIN
# =========================================================

def main():

    create_database()

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN not found in .env file."
        )

        return

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # GENERAL
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler("start", start)
    )

    # -----------------------------------------------------
    # STOCK
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler("stock", stock)
    )

    app.add_handler(
        CommandHandler("addproduct", addproduct)
    )

    app.add_handler(
        CommandHandler("receive", receive)
    )

    app.add_handler(
        CommandHandler("updateprice", updateprice)
    )

    app.add_handler(
        CommandHandler("setgst", setgst)
    )

    app.add_handler(
        CommandHandler("sell", sell)
    )

    app.add_handler(
        CommandHandler("lowstock", lowstock)
    )

    # -----------------------------------------------------
    # BILLING
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler("bill", bill)
    )

    app.add_handler(
        CommandHandler("additem", additem)
    )

    app.add_handler(
        CommandHandler("viewbill", viewbill)
    )

    app.add_handler(
        CommandHandler("removeitem", removeitem)
    )

    app.add_handler(
        CommandHandler("finalize", finalize)
    )

    # -----------------------------------------------------
    # CUSTOMER
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler("credit", credit)
    )

    app.add_handler(
        CommandHandler("payment", payment)
    )

    app.add_handler(
        CommandHandler("payments", payments)
    )

    app.add_handler(
        CommandHandler("balance", balance)
    )

    # -----------------------------------------------------
    # REPORTS
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler("sales", sales)
    )

    app.add_handler(
        CommandHandler("dailyclose", dailyclose)
    )

    # -----------------------------------------------------
    # NEW CHAT
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler("newchat", newchat)
    )

    # -----------------------------------------------------
    # AI AGENT
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler("ask", ask)
    )

    # -----------------------------------------------------
    # NORMAL TEXT → AI AGENT
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    print(
        "🤖 Supermarket Ops Agent is running..."
    )

    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()