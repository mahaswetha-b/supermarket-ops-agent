import os
import sqlite3
import requests

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

from database import (
    get_stock,
    add_product,
    sell_product,
    get_sales_summary,
    get_low_stock
)

from customer_account import (
    add_credit,
    make_payment,
    get_balance
)

from invoice import create_invoice
from sales_report import create_sales_report


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = """
🛒 Supermarket Ops Agent

Available Commands:

/stock <product>
/addproduct <name> <cost> <selling> <quantity>
/sell <product> <quantity>

/credit <customer> <amount>
/payment <customer> <amount>
/balance <customer>

/sales

/ask <question>
"""

    await update.message.reply_text(message)


async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "❌ Please enter product name.\n\n"
            "Example:\n"
            "/stock Maggi"
        )
        return

    product_name = " ".join(context.args)

    result = get_stock(product_name)

    if result is None:
        await update.message.reply_text(
            f"❌ Product '{product_name}' not found."
        )
        return

    await update.message.reply_text(
        f"📦 Product: {product_name}\n"
        f"📊 Stock: {result}"
    )


async def addproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 4:
        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Example:\n"
            "/addproduct apple juice 50 75 20"
        )
        return

    try:

        quantity = int(context.args[-1])
        selling_price = float(context.args[-2])
        cost_price = float(context.args[-3])

        product_name = " ".join(
            context.args[:-3]
        )

        add_product(
            product_name,
            cost_price,
            selling_price,
            quantity
        )

        await update.message.reply_text(
            f"✅ Product added successfully.\n\n"
            f"📦 Product: {product_name}\n"
            f"💰 Cost Price: ₹{cost_price}\n"
            f"🏷️ Selling Price: ₹{selling_price}\n"
            f"📊 Quantity Added: {quantity}"
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Cost price, selling price and quantity "
            "must be valid numbers."
        )


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Example:\n"
            "/sell apple juice 2"
        )
        return

    try:

        quantity = int(context.args[-1])

        product_name = " ".join(
            context.args[:-1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Quantity must be a number."
        )
        return

    stock_value = get_stock(product_name)

    if stock_value is None:

        await update.message.reply_text(
            f"❌ Product '{product_name}' not found."
        )
        return

    if quantity <= 0:

        await update.message.reply_text(
            "❌ Quantity must be greater than 0."
        )
        return

    if stock_value < quantity:

        await update.message.reply_text(
            f"❌ Not enough stock.\n"
            f"📦 Available: {stock_value} units"
        )
        return

    price = sell_product(
        product_name,
        quantity
    )

    if price is None:

        await update.message.reply_text(
            "❌ Sale could not be completed."
        )
        return

    total = price * quantity

    conn = sqlite3.connect(
        "supermarket.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT MAX(id) FROM bills"
    )

    result = cursor.fetchone()

    conn.close()

    bill_id = result[0]

    filename = create_invoice(
        bill_id,
        product_name,
        quantity,
        price,
        total
    )

    await update.message.reply_text(
        f"✅ Sale successful.\n\n"
        f"📦 Product: {product_name}\n"
        f"🔢 Quantity: {quantity}\n"
        f"💰 Price: ₹{price}\n"
        f"💵 Total: ₹{total}"
    )

    with open(filename, "rb") as document:

        await update.message.reply_document(
            document=document,
            caption=f"🧾 Invoice #{bill_id}"
        )


async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Example:\n"
            "/credit Ramesh 500"
        )
        return

    try:

        amount = float(context.args[-1])

        customer_name = " ".join(
            context.args[:-1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Amount must be a number."
        )
        return

    balance = add_credit(
        customer_name,
        amount
    )

    await update.message.reply_text(
        f"✅ Credit added.\n\n"
        f"👤 Customer: {customer_name}\n"
        f"💰 Credit: ₹{amount}\n"
        f"📊 Total Balance: ₹{balance}"
    )


async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Example:\n"
            "/payment Ramesh 300"
        )
        return

    try:

        amount = float(context.args[-1])

        customer_name = " ".join(
            context.args[:-1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Amount must be a number."
        )
        return

    remaining = make_payment(
        customer_name,
        amount
    )

    if remaining is None:

        await update.message.reply_text(
            f"❌ Customer '{customer_name}' not found."
        )
        return

    await update.message.reply_text(
        f"✅ Payment recorded.\n\n"
        f"👤 Customer: {customer_name}\n"
        f"💰 Paid: ₹{amount}\n"
        f"📊 Remaining Balance: ₹{remaining}"
    )


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
        f"💰 Outstanding Balance: ₹{result}"
    )


async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):

    summary = get_sales_summary()

    filename = create_sales_report()

    await update.message.reply_text(
        f"📊 Sales Summary\n\n"
        f"🧾 Bills: {summary[0]}\n"
        f"📦 Items Sold: {summary[1]}\n"
        f"💰 Total Sales: ₹{summary[2]}"
    )

    with open(filename, "rb") as document:

        await update.message.reply_document(
            document=document,
            caption="📊 Daily Sales Report"
        )


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "❌ Please ask a question.\n\n"
            "Example:\n"
            "/ask total sales"
        )
        return

    question = " ".join(
        context.args
    )

    q = question.lower()


    # TOTAL SALES

    if (
        "total sales" in q
        or "sales today" in q
        or "sales summary" in q
        or "how much sales" in q
        or "sales amount" in q
    ):

        summary = get_sales_summary()

        await update.message.reply_text(
            f"📊 Sales Summary\n\n"
            f"🧾 Bills: {summary[0]}\n"
            f"📦 Items Sold: {summary[1]}\n"
            f"💰 Total Sales: ₹{summary[2]}"
        )

        return


    # LOW STOCK

    if (
        "low stock" in q
        or "low-stock" in q
        or "low in stock" in q
        or "running low" in q
    ):

        products = get_low_stock()

        if not products:

            await update.message.reply_text(
                "✅ No products are currently low in stock."
            )

            return

        message = "⚠️ Low Stock Products:\n\n"

        for product in products:

            message += (
                f"📦 {product[0]}: "
                f"{product[1]}\n"
            )

        await update.message.reply_text(
            message
        )

        return


    # CURRENT INVENTORY

    inventory_phrases = [

        "current inventory",
        "show inventory",
        "display inventory",
        "list inventory",
        "what products are available",
        "which products are available",
        "list products",
        "show products",
        "all products"

    ]

    if any(
        phrase in q
        for phrase in inventory_phrases
    ):

        conn = sqlite3.connect(
            "supermarket.db"
        )

        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, SUM(quantity)
            FROM products
            GROUP BY LOWER(name)
            ORDER BY name
        """)

        products = cursor.fetchall()

        conn.close()

        if not products:

            await update.message.reply_text(
                "❌ No products found."
            )

            return

        message = "📦 Current Inventory:\n\n"

        for name, quantity in products:

            message += (
                f"• {name}: {quantity}\n"
            )

        await update.message.reply_text(
            message
        )

        return


    # PRODUCT STOCK QUESTIONS

    conn = sqlite3.connect(
        "supermarket.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT DISTINCT name FROM products"
    )

    product_names = [

        row[0]
        for row in cursor.fetchall()

    ]

    conn.close()

    for product_name in product_names:

        if product_name.lower() in q:

            stock_value = get_stock(
                product_name
            )

            await update.message.reply_text(
                f"📦 Product: {product_name}\n"
                f"📊 Stock: {stock_value}"
            )

            return


    # CUSTOMER BALANCE QUESTIONS

    conn = sqlite3.connect(
        "supermarket.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM customers"
    )

    customers = [

        row[0]
        for row in cursor.fetchall()

    ]

    conn.close()

    for customer_name in customers:

        if customer_name.lower() in q:

            balance_value = get_balance(
                customer_name
            )

            await update.message.reply_text(
                f"👤 Customer: {customer_name}\n"
                f"💰 Outstanding Balance: ₹{balance_value}"
            )

            return


    # LOCAL OLLAMA AI

    try:

        response = requests.post(

            "http://127.0.0.1:11434/api/generate",

            json={

                "model": "llama3.2",
                "prompt": question,
                "stream": False

            },

            timeout=120

        )

        response.raise_for_status()

        data = response.json()

        answer = data.get(

            "response",
            "Sorry, I could not generate an answer."

        )

        await update.message.reply_text(
            answer
        )

    except requests.exceptions.Timeout:

        await update.message.reply_text(
            "❌ AI response took too long. Please try again."
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ AI Error: {str(e)}"
        )


def main():

    app = ApplicationBuilder().token(
        BOT_TOKEN
    ).build()


    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("stock", stock)
    )

    app.add_handler(
        CommandHandler("addproduct", addproduct)
    )

    app.add_handler(
        CommandHandler("sell", sell)
    )

    app.add_handler(
        CommandHandler("credit", credit)
    )

    app.add_handler(
        CommandHandler("payment", payment)
    )

    app.add_handler(
        CommandHandler("balance", balance)
    )

    app.add_handler(
        CommandHandler("sales", sales)
    )

    app.add_handler(
        CommandHandler("ask", ask)
    )


    print(
        "🤖 Supermarket Ops Agent is running..."
    )

    app.run_polling()


if __name__ == "__main__":

    main()