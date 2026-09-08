import os
import re

from dotenv import load_dotenv

from database import (
    save_memory,
    get_all_memories,
    create_bill,
    add_bill_item,
    get_bill_items,
    get_bill_summary,
    remove_bill_item,
    finalize_bill,
    update_bill_payment,
)

from agent_tools import (
    stock_tool,
    product_details_tool,
    low_stock_tool,
    sales_summary_tool,
    add_product_tool,
    receive_stock_tool,
    sell_product_tool,
)

load_dotenv()


# ============================================================
# USER ID
# ============================================================

def normalize_user_id(user_id):

    if user_id is None:
        return 0

    if user_id == "default":
        return 0

    try:
        return int(user_id)
    except (ValueError, TypeError):
        return 0


# ============================================================
# MEMORY
# ============================================================

def load_user_memory(user_id):

    memory_user_id = normalize_user_id(user_id)

    try:
        return get_all_memories(memory_user_id)
    except Exception as e:
        print(f"[Memory] Error loading memory: {e}")
        return {}


def memory_context(user_id):

    memories = load_user_memory(user_id)

    if not memories:
        return "No saved user preferences."

    lines = []

    for key, value in memories.items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)


def detect_and_save_memory(user_id, user_message):

    memory_user_id = normalize_user_id(user_id)
    text = user_message.lower().strip()

    payment_preferences = {

        "upi": [
            "prefer upi",
            "prefer using upi",
            "prefer upi payment",
            "i like upi",
            "use upi",
        ],

        "cash": [
            "prefer cash",
            "prefer using cash",
            "prefer cash payment",
            "i like cash",
            "use cash",
        ],

        "card": [
            "prefer card",
            "prefer using card",
            "prefer card payment",
            "i like card",
            "use card",
        ],
    }

    for method, phrases in payment_preferences.items():

        if any(phrase in text for phrase in phrases):

            method_upper = method.upper()

            try:

                save_memory(
                    memory_user_id,
                    "preferred_payment_method",
                    method_upper,
                )

                print(
                    f"[Memory] Saved preferred payment: "
                    f"{method_upper}"
                )

            except Exception as e:

                print(
                    f"[Memory] Save error: {e}"
                )

            return method_upper

    if (
        "prefer tamil" in text
        or "speak tamil" in text
        or "reply in tamil" in text
        or "talk in tamil" in text
    ):

        try:

            save_memory(
                memory_user_id,
                "preferred_language",
                "Tamil",
            )

            print(
                "[Memory] Saved language preference: Tamil"
            )

        except Exception as e:

            print(
                f"[Memory] Save error: {e}"
            )

        return "Tamil"

    if (
        "prefer english" in text
        or "speak english" in text
        or "reply in english" in text
        or "talk in english" in text
    ):

        try:

            save_memory(
                memory_user_id,
                "preferred_language",
                "English",
            )

            print(
                "[Memory] Saved language preference: English"
            )

        except Exception as e:

            print(
                f"[Memory] Save error: {e}"
            )

        return "English"

    return None


def handle_memory_question(user_id, user_message):

    text = user_message.lower().strip()

    memories = load_user_memory(user_id)

    payment_question = (
        "preferred payment" in text
        or "prefer payment" in text
        or "payment method do i prefer" in text
        or "which payment" in text
        or "what payment" in text
    )

    if payment_question:

        payment = memories.get(
            "preferred_payment_method"
        )

        if payment:

            return (
                f"Your preferred payment method "
                f"is {payment}. 👍"
            )

        return (
            "You haven't saved a preferred "
            "payment method yet."
        )

    language_question = (
        "preferred language" in text
        or "what language" in text
        or "which language" in text
    )

    if language_question:

        language = memories.get(
            "preferred_language"
        )

        if language:

            return (
                f"Your preferred language "
                f"is {language}. 👍"
            )

        return (
            "You haven't saved a preferred "
            "language yet."
        )

    return None


# ============================================================
# PENDING ACTIONS
# ============================================================

pending_actions = {}


def get_pending_action(user_id):

    return pending_actions.get(user_id)


def set_pending_action(user_id, action):

    pending_actions[user_id] = action


def clear_pending_action(user_id):

    pending_actions.pop(user_id, None)


# ============================================================
# BILL STATE
# ============================================================

active_bills = {}


def get_active_bill(user_id):

    return active_bills.get(user_id)


def clear_active_bill(user_id):

    active_bills.pop(user_id, None)


def start_new_bill(user_id):

    bill_id = create_bill()

    active_bills[user_id] = bill_id

    return bill_id


# ============================================================
# FORMAT BILL
# ============================================================

def format_bill(user_id):

    bill_id = get_active_bill(user_id)

    if bill_id is None:

        return (
            "❌ No active bill.\n"
            "Type 'bill' to start a new bill."
        )

    try:

        items = get_bill_items(bill_id)
        summary = get_bill_summary(bill_id)

    except Exception as e:

        return (
            f"❌ Could not read bill: {e}"
        )

    if not items:

        return (
            "🧾 Current Bill\n\n"
            "No items added yet."
        )

    lines = [
        "🧾 CURRENT BILL",
        ""
    ]

    for item in items:

        name = item.get(
            "product_name",
            ""
        )

        qty = item.get(
            "quantity",
            0
        )

        total = item.get(
            "total",
            0
        )

        lines.append(
            f"• {name} × {qty} = ₹{float(total):.2f}"
        )

    lines.append("")

    if isinstance(summary, dict):

        bill_data = summary.get(
            "bill",
            summary
        )

        subtotal = bill_data.get(
            "subtotal",
            0
        )

        gst = bill_data.get(
            "gst_amount",
            bill_data.get(
                "total_gst",
                0
            )
        )

        cgst = bill_data.get(
            "cgst",
            0
        )

        sgst = bill_data.get(
            "sgst",
            0
        )

        grand_total = bill_data.get(
            "grand_total",
            0
        )

        lines.append(
            f"Subtotal: ₹{float(subtotal):.2f}"
        )

        lines.append(
            f"GST: ₹{float(gst):.2f}"
        )

        lines.append(
            f"CGST: ₹{float(cgst):.2f}"
        )

        lines.append(
            f"SGST: ₹{float(sgst):.2f}"
        )

        lines.append(
            f"Grand Total: ₹{float(grand_total):.2f}"
        )

    else:

        lines.append(
            str(summary)
        )

    return "\n".join(lines)


# ============================================================
# ADD ITEM TO BILL
# ============================================================

def handle_add_item(user_id, user_message):

    bill_id = get_active_bill(user_id)

    if bill_id is None:
        return None

    text = user_message.strip()

    # Bill control commands
    if text.lower() in [
        "bill",
        "new bill",
        "start bill",
        "finalize",
        "finalise",
        "view bill",
        "show bill",
        "remove item",
        "cancel bill",
    ]:
        return None

    # Example:
    # Maggi 2
    # Milk 1

    match = re.match(
        r"^(.+?)\s+(\d+(?:\.\d+)?)$",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    product_name = match.group(1).strip()

    quantity_text = match.group(2)

    try:

        quantity = float(
            quantity_text
        )

        if quantity.is_integer():
            quantity = int(quantity)

    except ValueError:

        return None

    if not product_name:

        return (
            "❌ Please provide a product name."
        )

    if quantity <= 0:

        return (
            "❌ Quantity must be greater than 0."
        )

    try:

        # Check product exists
        details = product_details_tool(
            product_name
        )

        if (
            not details
            or "not found" in str(details).lower()
        ):

            return (
                f"❌ Product '{product_name}' "
                f"not found."
            )

        print(
            "[Agent] Calling action: add_bill_item"
        )

        # IMPORTANT:
        # add_bill_item() returns None
        # when successful.
        #
        # Therefore DO NOT check:
        # if result is None -> failure
        #
        # If no exception occurs, it succeeded.

        add_bill_item(
            bill_id,
            product_name,
            quantity,
        )

        return (
            f"✅ Added to bill.\n\n"
            f"Product: {product_name}\n"
            f"Quantity: {quantity}\n\n"
            f"{format_bill(user_id)}"
        )

    except Exception as e:

        error = str(e)

        if "stock" in error.lower():

            return (
                f"❌ {error}"
            )

        if "not found" in error.lower():

            return (
                f"❌ {error}"
            )

        if "below cost" in error.lower():

            return (
                f"❌ {error}"
            )

        return (
            f"❌ Could not add item: {error}"
        )


# ============================================================
# REMOVE ITEM FROM BILL
# ============================================================

def handle_remove_item(user_id, user_message):

    bill_id = get_active_bill(user_id)

    if bill_id is None:
        return None

    text = user_message.strip()

    match = re.match(
        r"^(?:remove|delete)\s+(?:item\s+)?(.+)$",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    product_name = match.group(1).strip()

    if not product_name:

        return (
            "❌ Please provide the product name."
        )

    try:

        print(
            "[Agent] Calling action: "
            "remove_bill_item"
        )

        remove_bill_item(
            bill_id,
            product_name,
        )

        return (
            f"✅ Removed {product_name} "
            f"from the bill.\n\n"
            f"{format_bill(user_id)}"
        )

    except Exception as e:

        return (
            f"❌ Could not remove item: {e}"
        )


# ============================================================
# VIEW BILL
# ============================================================

def handle_view_bill(user_id, user_message):

    text = user_message.lower().strip()

    if text in [
        "view bill",
        "show bill",
        "view my bill",
        "show my bill",
        "bill summary",
    ]:

        if get_active_bill(user_id) is None:

            return (
                "❌ No active bill.\n"
                "Type 'bill' to start a new bill."
            )

        return format_bill(user_id)

    return None


# ============================================================
# FINALIZE BILL
# ============================================================

def handle_finalize(user_id, user_message):

    bill_id = get_active_bill(user_id)

    if bill_id is None:
        return None

    text = user_message.lower().strip()

    if text not in [
        "finalize",
        "finalise",
        "finish bill",
        "complete bill",
        "complete the bill",
    ]:
        return None

    try:

        items = get_bill_items(
            bill_id
        )

        if not items:

            return (
                "❌ Cannot finalize an empty bill.\n"
                "Add at least one item first."
            )

    except Exception as e:

        return (
            f"❌ Could not check bill items: {e}"
        )

    set_pending_action(
        user_id,
        {
            "action": "bill_payment",
            "bill_id": bill_id,
        },
    )

    return (
        f"{format_bill(user_id)}\n\n"
        "💳 Payment method?\n"
        "Choose: CASH, UPI, or CARD"
    )


# ============================================================
# BILL PAYMENT
# ============================================================

def handle_bill_payment(user_id, user_message):

    state = get_pending_action(user_id)

    if not state:
        return None

    if state.get("action") != "bill_payment":
        return None

    text = user_message.strip().upper()

    if text not in [
        "CASH",
        "UPI",
        "CARD",
    ]:

        return (
            "❌ Please choose a payment method:\n"
            "CASH, UPI, or CARD"
        )

    bill_id = state["bill_id"]

    try:

        print(
            "[Agent] Calling action: finalize_bill"
        )

        result = finalize_bill(
            bill_id,
            text,
            "",
        )

        clear_pending_action(
            user_id
        )

        clear_active_bill(
            user_id
        )

        grand_total = 0

        if isinstance(result, dict):

            grand_total = result.get(
                "grand_total",
                0
            )

        return (
            "✅ BILL FINALIZED SUCCESSFULLY\n\n"
            f"Bill ID: {bill_id}\n"
            f"Total: ₹{float(grand_total):.2f}\n"
            f"Payment: {text}\n\n"
            "Stock has been updated."
        )

    except TypeError:

        try:

            result = finalize_bill(
                bill_id,
                text,
            )

            clear_pending_action(
                user_id
            )

            clear_active_bill(
                user_id
            )

            grand_total = 0

            if isinstance(result, dict):

                grand_total = result.get(
                    "grand_total",
                    0
                )

            return (
                "✅ BILL FINALIZED SUCCESSFULLY\n\n"
                f"Bill ID: {bill_id}\n"
                f"Total: ₹{float(grand_total):.2f}\n"
                f"Payment: {text}\n\n"
                "Stock has been updated."
            )

        except Exception as e:

            return (
                f"❌ Bill finalization failed: {e}"
            )

    except Exception as e:

        return (
            f"❌ Bill finalization failed: {e}"
        )


# ============================================================
# ADD PRODUCT STATE
# ============================================================

def create_add_product_state(product_name):

    return {
        "action": "add_product",
        "product_name": product_name,
        "cost_price": None,
        "selling_price": None,
        "quantity": None,
        "hsn_code": "0000",
        "gst_rate": 0,
    }


# ============================================================
# RECEIVE STOCK STATE
# ============================================================

def create_receive_state(
    product_name,
    quantity
):

    return {
        "action": "receive_stock",
        "product_name": product_name,
        "quantity": quantity,
        "cost_price": None,
        "selling_price": None,
        "hsn_code": "0000",
        "gst_rate": 0,
    }


# ============================================================
# NUMBER EXTRACTION
# ============================================================

def extract_number(text):

    match = re.search(
        r"\d+(?:\.\d+)?",
        text,
    )

    if match:

        value = match.group(0)

        if "." in value:
            return float(value)

        return int(value)

    return None


# ============================================================
# ADD PRODUCT
# ============================================================

def handle_add_product(
    user_id,
    user_message
):

    state = get_pending_action(
        user_id
    )

    if state is not None:
        return None

    text = user_message.strip()

    lower_text = text.lower()

    prefixes = [
        "add a new product",
        "add new product",
        "add product",
    ]

    product_name = None

    for prefix in prefixes:

        if lower_text.startswith(prefix):

            product_name = text[
                len(prefix):
            ].strip()

            break

    if product_name:

        if product_name.lower().startswith(
            "called "
        ):

            product_name = product_name[
                len("called "):
            ].strip()

        product_name = product_name.strip(
            "\"'"
        )

        if not product_name:

            return (
                "Please provide the product name.\n"
                "Example: Add a new product called Biscuit"
            )

        state = create_add_product_state(
            product_name
        )

        set_pending_action(
            user_id,
            state,
        )

        return (
            f"Okay 👍 Adding product "
            f"'{product_name}'.\n\n"
            f"What is the cost price?"
        )

    return None


# ============================================================
# RECEIVE STOCK
# ============================================================

def handle_receive(
    user_id,
    user_message
):

    state = get_pending_action(
        user_id
    )

    if state is not None:
        return None

    pattern = re.search(
        r"receive\s+"
        r"(\d+(?:\.\d+)?)\s+"
        r"(.+)",
        user_message.strip(),
        re.IGNORECASE,
    )

    if not pattern:
        return None

    quantity = float(
        pattern.group(1)
    )

    product_name = pattern.group(
        2
    ).strip()

    if quantity.is_integer():
        quantity = int(quantity)

    state = create_receive_state(
        product_name,
        quantity,
    )

    set_pending_action(
        user_id,
        state,
    )

    return (
        f"Okay 👍 Receiving "
        f"{quantity} units of "
        f"{product_name}.\n\n"
        f"What is the cost price?"
    )


# ============================================================
# PENDING ACTION HANDLER
# ============================================================

def handle_pending_action(
    user_id,
    user_message
):

    state = get_pending_action(
        user_id
    )

    if state is None:
        return None

    # BILL PAYMENT

    if state.get("action") == "bill_payment":

        return handle_bill_payment(
            user_id,
            user_message,
        )

    number = extract_number(
        user_message
    )

    # ========================================================
    # ADD PRODUCT
    # ========================================================

    if state["action"] == "add_product":

        if state["cost_price"] is None:

            if number is None:

                return (
                    "Please enter the cost price.\n"
                    "Example: 10"
                )

            state["cost_price"] = number

            return (
                "What is the selling price?"
            )

        if state["selling_price"] is None:

            if number is None:

                return (
                    "Please enter the selling price.\n"
                    "Example: 15"
                )

            if number < state["cost_price"]:

                return (
                    "❌ Selling price cannot be "
                    "lower than cost price.\n\n"
                    "Please enter a valid selling price."
                )

            state["selling_price"] = number

            return (
                "What is the quantity?"
            )

        if state["quantity"] is None:

            if number is None:

                return (
                    "Please enter the quantity.\n"
                    "Example: 20"
                )

            if number <= 0:

                return (
                    "❌ Quantity must be greater than 0."
                )

            state["quantity"] = number

            print(
                "[Agent] Calling action: "
                "add_product_tool"
            )

            result = add_product_tool(
                product_name=state[
                    "product_name"
                ],
                cost_price=state[
                    "cost_price"
                ],
                selling_price=state[
                    "selling_price"
                ],
                quantity=state[
                    "quantity"
                ],
                hsn_code=state[
                    "hsn_code"
                ],
                gst_rate=state[
                    "gst_rate"
                ],
            )

            clear_pending_action(
                user_id
            )

            return result

    # ========================================================
    # RECEIVE STOCK
    # ========================================================

    if state["action"] == "receive_stock":

        if state["cost_price"] is None:

            if number is None:

                return (
                    "Please enter the cost price.\n"
                    "Example: 10"
                )

            state["cost_price"] = number

            return (
                "What is the selling price?"
            )

        if state["selling_price"] is None:

            if number is None:

                return (
                    "Please enter the selling price.\n"
                    "Example: 15"
                )

            if number < state["cost_price"]:

                return (
                    "❌ Selling price cannot be "
                    "lower than cost price.\n\n"
                    "Please enter a valid selling price."
                )

            state["selling_price"] = number

            print(
                "[Agent] Calling action: "
                "receive_stock_tool"
            )

            result = receive_stock_tool(
                product_name=state[
                    "product_name"
                ],
                quantity=state[
                    "quantity"
                ],
                cost_price=state[
                    "cost_price"
                ],
                selling_price=state[
                    "selling_price"
                ],
                hsn_code=state[
                    "hsn_code"
                ],
                gst_rate=state[
                    "gst_rate"
                ],
            )

            clear_pending_action(
                user_id
            )

            return result

    return None


# ============================================================
# SELL PRODUCT
# ============================================================

def handle_sell(
    user_id,
    user_message
):

    text = user_message.strip()

    match = re.match(
        r"^sell\s+"
        r"(.+?)\s+"
        r"(\d+(?:\.\d+)?)$",
        text,
        re.IGNORECASE,
    )

    if match:

        product_name = match.group(
            1
        ).strip()

        quantity = float(
            match.group(2)
        )

        if quantity.is_integer():
            quantity = int(quantity)

        if not product_name:

            return (
                "❌ Please provide the product name."
            )

        print(
            "[Agent] Calling action: "
            "sell_product_tool"
        )

        return sell_product_tool(
            product_name=product_name,
            quantity=quantity,
        )

    match = re.match(
        r"^sell\s+(.+)$",
        text,
        re.IGNORECASE,
    )

    if match:

        product_name = match.group(
            1
        ).strip()

        if product_name:

            return (
                f"How many units of "
                f"{product_name} "
                f"would you like to sell?"
            )

    return None


# ============================================================
# STOCK PRODUCT EXTRACTION
# ============================================================

def extract_stock_product(text):

    patterns = [

        r"stock\s+(?:of\s+)?(.+)",

        r"how many\s+(.+)\s+"
        r"(?:do we have|are there)",

        r"how much\s+(.+)\s+"
        r"(?:do we have|is left)",

        r"quantity\s+(?:of\s+)?(.+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            product = match.group(
                1
            ).strip()

            product = re.sub(
                r"\?$",
                "",
                product,
            ).strip()

            if product:
                return product

    return None


def is_stock_question(text):

    lower = text.lower()

    return (
        "stock" in lower
        or "how many" in lower
        or "quantity of" in lower
        or "how much" in lower
    )


# ============================================================
# PRODUCT DETAILS
# ============================================================

def extract_product_details_name(text):

    patterns = [

        r"details\s+(?:of\s+)?(.+)",

        r"information\s+(?:about|on)\s+(.+)",

        r"product\s+details\s+(?:of\s+)?(.+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            product = match.group(
                1
            ).strip()

            product = re.sub(
                r"\?$",
                "",
                product,
            ).strip()

            if product:
                return product

    return None


# ============================================================
# NORMAL AGENT
# ============================================================

def run_normal_agent(
    user_id,
    user_message
):

    memory_answer = handle_memory_question(
        user_id,
        user_message,
    )

    if memory_answer is not None:
        return memory_answer

    # ========================================================
    # STOCK
    # ========================================================

    if is_stock_question(
        user_message
    ):

        product_name = extract_stock_product(
            user_message
        )

        if product_name:

            print(
                "[Agent] Calling tool: stock_tool"
            )

            try:

                return str(
                    stock_tool(
                        product_name
                    )
                )

            except Exception as e:

                return (
                    f"❌ Stock tool error: {e}"
                )

    # ========================================================
    # PRODUCT DETAILS
    # ========================================================

    product_name = extract_product_details_name(
        user_message
    )

    if product_name:

        print(
            "[Agent] Calling tool: "
            "product_details_tool"
        )

        try:

            return str(
                product_details_tool(
                    product_name
                )
            )

        except Exception as e:

            return (
                f"❌ Product details error: {e}"
            )

    # ========================================================
    # LOW STOCK
    # ========================================================

    lower = user_message.lower()

    if (
        "low stock" in lower
        or "low-stock" in lower
        or "which products are low" in lower
        or "products are low" in lower
    ):

        print(
            "[Agent] Calling tool: "
            "low_stock_tool"
        )

        try:

            return str(
                low_stock_tool()
            )

        except Exception as e:

            return (
                f"❌ Low stock tool error: {e}"
            )

    # ========================================================
    # SALES
    # ========================================================

    sales_question = (
        lower == "sales"
        or "sales summary" in lower
        or "today's sales" in lower
        or "todays sales" in lower
        or "daily sales" in lower
        or "sales report" in lower
    )

    if sales_question:

        print(
            "[Agent] Calling tool: "
            "sales_summary_tool"
        )

        try:

            return str(
                sales_summary_tool()
            )

        except Exception as e:

            return (
                f"❌ Sales tool error: {e}"
            )

    # ========================================================
    # OLLAMA FALLBACK
    # ========================================================

    try:

        import ollama

    except ImportError:

        return (
            "I couldn't understand the request.\n"
            "You can ask things like:\n"
            "- What is the stock of Biscuit?\n"
            "- Show low stock\n"
            "- Show sales\n"
            "- Sell Biscuit 2\n"
            "- Bill"
        )

    memories = memory_context(
        user_id
    )

    system_prompt = f"""
You are Supermarket Ops Agent.

You help operate an Indian supermarket/kirana store.

Rules:

1. Use INR (₹).
2. Be concise and helpful.
3. Never invent stock information.
4. Never invent sales information.
5. Never invent prices.
6. Never guess product names.
7. Never pretend a sale happened.
8. Inventory-changing actions are handled by application tools.
9. Multi-item billing is handled by application logic.
10. Never invent bill items or totals.
11. Never pretend a bill was finalized.
12. Never invent payment information.

Saved user memory:

{memories}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    try:

        response = ollama.chat(
            model="llama3.2",
            messages=messages,
        )

        message = response.get(
            "message",
            {}
        )

        answer = message.get(
            "content",
            ""
        )

        if answer:
            return answer

        return (
            "I couldn't understand that."
        )

    except Exception as e:

        return (
            f"❌ Ollama error: {e}"
        )


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent(
    question,
    user_id="default"
):

    normalized_id = normalize_user_id(
        user_id
    )

    detect_and_save_memory(
        normalized_id,
        question,
    )

    # ========================================================
    # PENDING ACTION
    # ========================================================

    pending_result = handle_pending_action(
        normalized_id,
        question,
    )

    if pending_result is not None:
        return pending_result

    lower = question.lower().strip()

    # ========================================================
    # START NEW BILL
    # ========================================================

    if lower in [
        "bill",
        "new bill",
        "start bill",
        "start a bill",
    ]:

        try:

            old_bill = get_active_bill(
                normalized_id
            )

            if old_bill is not None:

                return (
                    "⚠️ You already have an active bill.\n\n"
                    f"{format_bill(normalized_id)}"
                )

            bill_id = start_new_bill(
                normalized_id
            )

            return (
                "🧾 NEW BILL STARTED\n\n"
                f"Bill ID: {bill_id}\n\n"
                "Add items like:\n"
                "• Maggi 2\n"
                "• Milk 1\n\n"
                "Then type 'view bill' "
                "or 'finalize'."
            )

        except Exception as e:

            return (
                f"❌ Could not start bill: {e}"
            )

    # ========================================================
    # VIEW BILL
    # ========================================================

    view_result = handle_view_bill(
        normalized_id,
        question,
    )

    if view_result is not None:
        return view_result

    # ========================================================
    # REMOVE ITEM
    # ========================================================

    remove_result = handle_remove_item(
        normalized_id,
        question,
    )

    if remove_result is not None:
        return remove_result

    # ========================================================
    # FINALIZE
    # ========================================================

    finalize_result = handle_finalize(
        normalized_id,
        question,
    )

    if finalize_result is not None:
        return finalize_result

    # ========================================================
    # ADD ITEM TO ACTIVE BILL
    # ========================================================

    if get_active_bill(
        normalized_id
    ) is not None:

        add_item_result = handle_add_item(
            normalized_id,
            question,
        )

        if add_item_result is not None:
            return add_item_result

    # ========================================================
    # ADD PRODUCT
    # ========================================================

    add_result = handle_add_product(
        normalized_id,
        question,
    )

    if add_result is not None:
        return add_result

    # ========================================================
    # RECEIVE STOCK
    # ========================================================

    receive_result = handle_receive(
        normalized_id,
        question,
    )

    if receive_result is not None:
        return receive_result

    # ========================================================
    # SELL PRODUCT
    # ========================================================

    sell_result = handle_sell(
        normalized_id,
        question,
    )

    if sell_result is not None:
        return sell_result

    # ========================================================
    # NORMAL AGENT
    # ========================================================

    return run_normal_agent(
        normalized_id,
        question,
    )


# ============================================================
# NEW CHAT
# ============================================================

conversation_state = {}


def clear_conversation(
    user_id="default"
):

    normalized_id = normalize_user_id(
        user_id
    )

    conversation_state.pop(
        normalized_id,
        None,
    )

    clear_pending_action(
        normalized_id
    )

    clear_active_bill(
        normalized_id
    )

    return (
        "New chat started. "
        "Your saved preferences are "
        "still remembered. 👍"
    )


# ============================================================
# TERMINAL
# ============================================================

if __name__ == "__main__":

    TEST_USER_ID = 0

    print("=" * 60)
    print("SUPERMARKET OPS AGENT")
    print("=" * 60)

    print(
        "Type 'exit' to stop."
    )

    print(
        "Type 'new chat' to clear conversation."
    )

    print()

    while True:

        try:

            question = input(
                "You: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError,
        ):

            print(
                "\nGoodbye 👋"
            )

            break

        if not question:
            continue

        if question.lower() in [
            "exit",
            "quit",
            "bye",
        ]:

            print(
                "Goodbye 👋"
            )

            break

        if question.lower() in [
            "new chat",
            "/new chat",
        ]:

            print(
                clear_conversation(
                    TEST_USER_ID
                )
            )

            continue

        answer = run_agent(
            question,
            TEST_USER_ID,
        )

        print()
        print(
            "Agent:",
            answer,
        )
        print()