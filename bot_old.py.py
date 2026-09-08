import os

from dotenv import load_dotenv
from openai import OpenAI

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from database import (
    get_stock,
    add_product,
    sell_product,
    get_sales_summary
)

from customer_account import (
    add_credit,
    make_payment,
    get_balance
)

from invoice import create_invoice
from sales_report import create_sales_report


# LOAD ENVIRONMENT VARIABLES
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# OPENAI CLIENT
client = OpenAI()


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Welcome to Supermarket Ops Agent! 🛒\n\n"
        "Commands:\n"
        "/stock Maggi\n"
        "/addproduct Milk 25 30 50\n"
        "/sell Maggi 2\n"
        "/credit Ramesh 500\n"
        "/payment Ramesh 300\n"
        "/balance Ramesh\n"
        "/sales\n"
        "/ask your question"
    )


# STOCK COMMAND
async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "Please enter product name.\n"
            "Example: /stock Maggi"
        )
        return

    product_name = " ".join(context.args)

    product = get_stock(product_name)

    if not product:
        await update.message.reply_text(
            f"{product_name} not found in stock."
        )
        return

    product_id, name, price, quantity = product

    await update.message.reply_text(
        f"📦 Product: {name}\n"
        f"💰 Price: ₹{price}\n"
        f"📊 Available Stock: {quantity}"
    )


# ADD PRODUCT COMMAND
async def addproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 4:

        await update.message.reply_text(
            "Wrong format!\n\n"
            "Use:\n"
            "/addproduct ProductName CostPrice SellingPrice Quantity\n\n"
            "Example:\n"
            "/addproduct Milk 25 30 50"
        )
        return

    try:

        name = context.args[0]
        cost_price = float(context.args[1])
        selling_price = float(context.args[2])
        quantity = int(context.args[3])

        add_product(
            name,
            cost_price,
            selling_price,
            quantity
        )

        await update.message.reply_text(
            f"✅ Product added successfully!\n\n"
            f"📦 Product: {name}\n"
            f"💵 Cost Price: ₹{cost_price}\n"
            f"💰 Selling Price: ₹{selling_price}\n"
            f"📊 Quantity: {quantity}"
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Please enter valid numbers."
        )


# SELL PRODUCT COMMAND
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 2:

        await update.message.reply_text(
            "Wrong format!\n\n"
            "Use:\n"
            "/sell ProductName Quantity\n\n"
            "Example: /sell Maggi 2"
        )
        return

    product_name = context.args[0]

    try:
        quantity = int(context.args[1])

    except ValueError:

        await update.message.reply_text(
            "❌ Quantity must be a number."
        )
        return

    result, error = sell_product(
        product_name,
        quantity
    )

    if error:

        await update.message.reply_text(
            f"❌ {error}"
        )
        return

    await update.message.reply_text(
        f"🧾 Sale Successful!\n\n"
        f"🆔 Bill ID: {result['bill_id']}\n"
        f"📦 Product: {result['name']}\n"
        f"🔢 Quantity: {result['quantity']}\n"
        f"💰 Price: ₹{result['price']}\n"
        f"💵 Total: ₹{result['total']}\n"
        f"📊 Remaining Stock: {result['remaining_stock']}"
    )

    # CREATE AND SEND INVOICE
    try:

        invoice_file = create_invoice(
            result["bill_id"],
            result["name"],
            result["quantity"],
            result["price"],
            result["total"]
        )

        with open(invoice_file, "rb") as pdf:

            await update.message.reply_document(
                document=pdf,
                caption=f"🧾 Invoice for Bill #{result['bill_id']}"
            )

    except Exception as e:

        await update.message.reply_text(
            "⚠️ Sale completed, but invoice could not be sent.\n"
            f"Error: {e}"
        )


# CREDIT COMMAND
async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 2:

        await update.message.reply_text(
            "Wrong format!\n\n"
            "Example:\n"
            "/credit Ramesh 500"
        )
        return

    customer_name = context.args[0]

    try:

        amount = float(context.args[1])

        if amount <= 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            "❌ Enter a valid amount."
        )
        return

    balance = add_credit(
        customer_name,
        amount
    )

    await update.message.reply_text(
        f"📒 Credit Added\n\n"
        f"👤 Customer: {customer_name}\n"
        f"💵 Added: ₹{amount}\n"
        f"💰 Total Balance: ₹{balance}"
    )


# PAYMENT COMMAND
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 2:

        await update.message.reply_text(
            "Wrong format!\n\n"
            "Example:\n"
            "/payment Ramesh 300"
        )
        return

    customer_name = context.args[0]

    try:

        amount = float(context.args[1])

        if amount <= 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            "❌ Enter a valid amount."
        )
        return

    balance = make_payment(
        customer_name,
        amount
    )

    if balance is None:

        await update.message.reply_text(
            f"❌ Customer {customer_name} not found."
        )
        return

    await update.message.reply_text(
        f"💳 Payment Recorded\n\n"
        f"👤 Customer: {customer_name}\n"
        f"💵 Paid: ₹{amount}\n"
        f"💰 Remaining Balance: ₹{balance}"
    )


# BALANCE COMMAND
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Wrong format!\n\n"
            "Example:\n"
            "/balance Ramesh"
        )
        return

    customer_name = context.args[0]

    customer = get_balance(
        customer_name
    )

    if not customer:

        await update.message.reply_text(
            f"❌ Customer {customer_name} not found."
        )
        return

    await update.message.reply_text(
        f"📒 Customer Khata\n\n"
        f"👤 Name: {customer[0]}\n"
        f"💰 Balance Due: ₹{customer[1]}"
    )


# SALES COMMAND
async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):

    summary = get_sales_summary()

    total_bills = summary[0]
    items_sold = summary[1]
    total_sales = summary[2]

    await update.message.reply_text(
        f"📊 Daily Sales Summary\n\n"
        f"🧾 Total Bills: {total_bills}\n"
        f"📦 Items Sold: {items_sold}\n"
        f"💰 Total Sales: ₹{total_sales}"
    )

    # CREATE AND SEND SALES REPORT
    try:

        report_file = create_sales_report()

        with open(report_file, "rb") as pdf:

            await update.message.reply_document(
                document=pdf,
                caption="📊 Daily Sales Report"
            )

    except Exception as e:

        await update.message.reply_text(
            "⚠️ Sales summary generated, but PDF report could not be sent.\n"
            f"Error: {e}"
        )


# AI ASK COMMAND
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "Please ask a question.\n\n"
            "Example:\n"
            "/ask What is the use of inventory management?"
        )
        return

    question = " ".join(context.args)

    try:

        response = client.responses.create(
            model="gpt-5-mini",
            input=(
                "You are a helpful supermarket operations assistant. "
                "Answer the user's question clearly and briefly.\n\n"
                f"User question: {question}"
            )
        )

        answer = response.output_text

        await update.message.reply_text(
            f"🤖 {answer}"
        )

    except Exception as e:

        await update.message.reply_text(
            "❌ AI response failed.\n"
            f"Error: {e}"
        )


# MAIN
def main():

    app = Application.builder().token(TOKEN).build()

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

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()