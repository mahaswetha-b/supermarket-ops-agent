import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

DB_NAME = "supermarket.db"


# =========================================================
# CONNECTION
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


# =========================================================
# HELPERS
# =========================================================

def money(value):
    return float(
        Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    )


def calculate_gst(subtotal, gst_rate):
    gst = money(float(subtotal) * float(gst_rate) / 100)
    cgst = money(gst / 2)
    sgst = money(gst - cgst)
    return gst, cgst, sgst


# =========================================================
# DATABASE
# =========================================================

def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            quantity INTEGER DEFAULT 0,
            hsn_code TEXT DEFAULT '0000',
            gst_rate REAL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_date TEXT,
            subtotal REAL DEFAULT 0,
            gst_amount REAL DEFAULT 0,
            grand_total REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'CASH',
            payment_reference TEXT DEFAULT '',
            transaction_id TEXT UNIQUE,
            total_gst REAL DEFAULT 0,
            cgst REAL DEFAULT 0,
            sgst REAL DEFAULT 0,
            bill_type TEXT DEFAULT 'HEADER'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            hsn_code TEXT DEFAULT '0000',
            gst_rate REAL DEFAULT 0,
            gst_amount REAL DEFAULT 0,
            FOREIGN KEY (bill_id)
                REFERENCES bills(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            memory_key TEXT NOT NULL,
            memory_value TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, memory_key)
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# MEMORY
# =========================================================

def save_memory(user_id, memory_key, memory_value):

    create_database()

    conn = get_connection()

    conn.execute("""
        INSERT INTO user_memory
        (user_id, memory_key, memory_value)
        VALUES (?, ?, ?)

        ON CONFLICT(user_id, memory_key)
        DO UPDATE SET
            memory_value = excluded.memory_value,
            updated_at = CURRENT_TIMESTAMP
    """, (
        int(user_id),
        str(memory_key).strip(),
        str(memory_value).strip()
    ))

    conn.commit()
    conn.close()


def get_memory(user_id, memory_key):

    create_database()

    conn = get_connection()

    row = conn.execute("""
        SELECT memory_value
        FROM user_memory
        WHERE user_id = ?
        AND memory_key = ?
    """, (
        int(user_id),
        str(memory_key).strip()
    )).fetchone()

    conn.close()

    return row["memory_value"] if row else None


def get_all_memories(user_id):

    create_database()

    conn = get_connection()

    rows = conn.execute("""
        SELECT memory_key, memory_value
        FROM user_memory
        WHERE user_id = ?
    """, (int(user_id),)).fetchall()

    conn.close()

    return {
        row["memory_key"]: row["memory_value"]
        for row in rows
    }


def delete_memory(user_id, memory_key):

    create_database()

    conn = get_connection()

    conn.execute("""
        DELETE FROM user_memory
        WHERE user_id = ?
        AND memory_key = ?
    """, (
        int(user_id),
        str(memory_key).strip()
    ))

    conn.commit()
    conn.close()


# =========================================================
# PRODUCTS
# =========================================================

def add_product(
    name,
    cost_price,
    selling_price,
    quantity,
    hsn_code="0000",
    gst_rate=0
):

    create_database()

    name = name.strip()
    cost_price = money(cost_price)
    selling_price = money(selling_price)
    quantity = int(quantity)

    if not name:
        raise ValueError("Product name cannot be empty.")

    if cost_price <= 0:
        raise ValueError("Cost price must be greater than 0.")

    if selling_price <= 0:
        raise ValueError("Selling price must be greater than 0.")

    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    if selling_price < cost_price:
        raise ValueError(
            "Selling price cannot be lower than cost price."
        )

    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO products
            (name, cost_price, selling_price, quantity, hsn_code, gst_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            cost_price,
            selling_price,
            quantity,
            hsn_code,
            float(gst_rate)
        ))

        conn.commit()

    except sqlite3.IntegrityError:
        raise ValueError(
            f"Product '{name}' already exists."
        )

    finally:
        conn.close()


def receive_stock(
    name,
    quantity,
    cost_price,
    selling_price,
    hsn_code="0000",
    gst_rate=0
):

    create_database()

    name = name.strip()
    quantity = int(quantity)
    cost_price = money(cost_price)
    selling_price = money(selling_price)

    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    if cost_price <= 0:
        raise ValueError("Cost price must be greater than 0.")

    if selling_price <= 0:
        raise ValueError("Selling price must be greater than 0.")

    if selling_price < cost_price:
        raise ValueError(
            "Selling price cannot be lower than cost price."
        )

    conn = get_connection()

    try:

        existing = conn.execute("""
            SELECT *
            FROM products
            WHERE LOWER(name) = LOWER(?)
        """, (name,)).fetchone()

        if existing:

            conn.execute("""
                UPDATE products
                SET
                    quantity = quantity + ?,
                    cost_price = ?,
                    selling_price = ?,
                    hsn_code = ?,
                    gst_rate = ?
                WHERE id = ?
            """, (
                quantity,
                cost_price,
                selling_price,
                hsn_code,
                float(gst_rate),
                existing["id"]
            ))

        else:

            conn.execute("""
                INSERT INTO products
                (name, cost_price, selling_price, quantity, hsn_code, gst_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name,
                cost_price,
                selling_price,
                quantity,
                hsn_code,
                float(gst_rate)
            ))

        conn.commit()

    finally:
        conn.close()


def get_stock(product_name):

    create_database()

    conn = get_connection()

    row = conn.execute("""
        SELECT name, quantity
        FROM products
        WHERE LOWER(name) = LOWER(?)
    """, (product_name.strip(),)).fetchone()

    conn.close()

    if not row:
        return f"Product '{product_name}' not found."

    return (
        f"Product: {row['name']}\n"
        f"Stock: {row['quantity']}"
    )


def get_product_details(product_name):

    create_database()

    conn = get_connection()

    row = conn.execute("""
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
    """, (product_name.strip(),)).fetchone()

    conn.close()

    if not row:
        return f"Product '{product_name}' not found."

    return (
        f"Product: {row['name']}\n"
        f"Stock: {row['quantity']}\n"
        f"Cost Price: ₹{row['cost_price']:.2f}\n"
        f"Selling Price: ₹{row['selling_price']:.2f}\n"
        f"HSN: {row['hsn_code']}\n"
        f"GST: {row['gst_rate']:.2f}%"
    )


def update_price(product_name, selling_price):

    create_database()

    selling_price = money(selling_price)

    conn = get_connection()

    row = conn.execute("""
        SELECT cost_price
        FROM products
        WHERE LOWER(name) = LOWER(?)
    """, (product_name.strip(),)).fetchone()

    if not row:
        conn.close()
        raise ValueError(
            f"Product '{product_name}' not found."
        )

    if selling_price < row["cost_price"]:
        conn.close()
        raise ValueError(
            f"Selling price ₹{selling_price:.2f} "
            f"cannot be below cost price "
            f"₹{row['cost_price']:.2f}."
        )

    conn.execute("""
        UPDATE products
        SET selling_price = ?
        WHERE LOWER(name) = LOWER(?)
    """, (
        selling_price,
        product_name.strip()
    ))

    conn.commit()
    conn.close()


def set_product_gst(product_name, hsn_code, gst_rate):

    create_database()

    gst_rate = float(gst_rate)

    if gst_rate < 0 or gst_rate > 100:
        raise ValueError(
            "GST rate must be between 0 and 100."
        )

    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM products
        WHERE LOWER(name) = LOWER(?)
    """, (product_name.strip(),)).fetchone()

    if not row:
        conn.close()
        raise ValueError(
            f"Product '{product_name}' not found."
        )

    conn.execute("""
        UPDATE products
        SET hsn_code = ?, gst_rate = ?
        WHERE id = ?
    """, (
        hsn_code,
        gst_rate,
        row["id"]
    ))

    conn.commit()
    conn.close()


set_gst = set_product_gst


# =========================================================
# LOW STOCK
# =========================================================

def get_low_stock(threshold=10):

    create_database()

    conn = get_connection()

    rows = conn.execute("""
        SELECT name, quantity, selling_price
        FROM products
        WHERE quantity <= ?
        ORDER BY quantity ASC, name ASC
    """, (threshold,)).fetchall()

    conn.close()

    if not rows:
        return "No low-stock products."

    result = [
        "Low Stock Products",
        "-------------------"
    ]

    for row in rows:
        result.append(
            f"{row['name']} - "
            f"Stock: {row['quantity']} - "
            f"Price: ₹{row['selling_price']:.2f}"
        )

    return "\n".join(result)


# =========================================================
# TRANSACTION
# =========================================================

def transaction_exists(transaction_id):

    if not transaction_id:
        return False

    create_database()

    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM transaction_log
        WHERE transaction_id = ?
    """, (transaction_id,)).fetchone()

    conn.close()

    return row is not None


def record_transaction(transaction_id):

    if not transaction_id:
        return

    create_database()

    conn = get_connection()

    conn.execute("""
        INSERT OR IGNORE INTO transaction_log
        (transaction_id)
        VALUES (?)
    """, (transaction_id,))

    conn.commit()
    conn.close()


# =========================================================
# SINGLE ITEM SALE
# =========================================================

def sell_product(
    product_name,
    quantity,
    transaction_id=None,
    payment_method="CASH",
    payment_reference=""
):

    create_database()

    quantity = int(quantity)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than 0."
        )

    if transaction_id and transaction_exists(transaction_id):

        conn = get_connection()

        row = conn.execute("""
            SELECT *
            FROM bills
            WHERE transaction_id = ?
        """, (transaction_id,)).fetchone()

        conn.close()

        if row:
            return dict(row)

        raise ValueError(
            "Transaction already processed."
        )

    conn = get_connection()

    try:

        conn.execute("BEGIN IMMEDIATE")

        product = conn.execute("""
            SELECT *
            FROM products
            WHERE LOWER(name) = LOWER(?)
        """, (product_name.strip(),)).fetchone()

        if not product:
            raise ValueError(
                f"Product '{product_name}' not found."
            )

        if product["quantity"] < quantity:
            raise ValueError(
                f"Insufficient stock for {product['name']}. "
                f"Available: {product['quantity']}, "
                f"Requested: {quantity}"
            )

        cost_price = float(product["cost_price"])
        selling_price = float(product["selling_price"])

        if selling_price < cost_price:
            raise ValueError(
                f"Sale blocked. Selling price "
                f"₹{selling_price:.2f} is below cost price "
                f"₹{cost_price:.2f}."
            )

        subtotal = money(
            selling_price * quantity
        )

        gst, cgst, sgst = calculate_gst(
            subtotal,
            product["gst_rate"]
        )

        grand_total = money(
            subtotal + gst
        )

        cursor = conn.execute("""
            UPDATE products
            SET quantity = quantity - ?
            WHERE id = ?
            AND quantity >= ?
        """, (
            quantity,
            product["id"],
            quantity
        ))

        if cursor.rowcount != 1:
            raise ValueError(
                "Stock changed during sale. Please try again."
            )

        bill_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor = conn.execute("""
            INSERT INTO bills
            (
                bill_date,
                subtotal,
                gst_amount,
                grand_total,
                payment_method,
                payment_reference,
                transaction_id,
                total_gst,
                cgst,
                sgst,
                bill_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'FINAL')
        """, (
            bill_date,
            subtotal,
            gst,
            grand_total,
            payment_method.upper(),
            payment_reference,
            transaction_id,
            gst,
            cgst,
            sgst
        ))

        bill_id = cursor.lastrowid

        conn.execute("""
            INSERT INTO bill_items
            (
                bill_id,
                product_name,
                quantity,
                price,
                total,
                hsn_code,
                gst_rate,
                gst_amount
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bill_id,
            product["name"],
            quantity,
            selling_price,
            subtotal,
            product["hsn_code"],
            product["gst_rate"],
            gst
        ))

        if transaction_id:
            conn.execute("""
                INSERT INTO transaction_log
                (transaction_id)
                VALUES (?)
            """, (transaction_id,))

        conn.commit()

        return {
            "id": bill_id,
            "bill_id": bill_id,
            "product_name": product["name"],
            "quantity": quantity,
            "price": selling_price,
            "subtotal": subtotal,
            "gst_amount": gst,
            "cgst": cgst,
            "sgst": sgst,
            "grand_total": grand_total,
            "payment_method": payment_method.upper(),
            "payment_reference": payment_reference,
            "remaining_stock": product["quantity"] - quantity
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================================================
# MULTI ITEM BILL
# =========================================================

def create_bill(transaction_id=None):

    create_database()

    conn = get_connection()

    try:

        bill_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor = conn.execute("""
            INSERT INTO bills
            (
                bill_date,
                subtotal,
                gst_amount,
                grand_total,
                payment_method,
                payment_reference,
                transaction_id,
                total_gst,
                cgst,
                sgst,
                bill_type
            )
            VALUES (?, 0, 0, 0, 'CASH', '', ?, 0, 0, 0, 'HEADER')
        """, (
            bill_date,
            transaction_id
        ))

        bill_id = cursor.lastrowid

        conn.commit()

        return bill_id

    finally:
        conn.close()


def add_bill_item(
    bill_id,
    product_name,
    quantity
):

    create_database()

    quantity = int(quantity)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than 0."
        )

    conn = get_connection()

    try:

        bill = conn.execute("""
            SELECT id, bill_type
            FROM bills
            WHERE id = ?
        """, (bill_id,)).fetchone()

        if not bill:
            raise ValueError(
                f"Bill {bill_id} not found."
            )

        if bill["bill_type"] == "FINAL":
            raise ValueError(
                "This bill is already finalized."
            )

        product = conn.execute("""
            SELECT *
            FROM products
            WHERE LOWER(name) = LOWER(?)
        """, (product_name.strip(),)).fetchone()

        if not product:
            raise ValueError(
                f"Product '{product_name}' not found."
            )

        if product["selling_price"] < product["cost_price"]:
            raise ValueError(
                f"Sale blocked. Selling price "
                f"₹{product['selling_price']:.2f} "
                f"is below cost price "
                f"₹{product['cost_price']:.2f}."
            )

        existing = conn.execute("""
            SELECT id, quantity
            FROM bill_items
            WHERE bill_id = ?
            AND LOWER(product_name) = LOWER(?)
        """, (
            bill_id,
            product["name"]
        )).fetchone()

        new_quantity = quantity

        if existing:
            new_quantity = (
                existing["quantity"] + quantity
            )

        if new_quantity > product["quantity"]:
            raise ValueError(
                f"Insufficient stock for {product['name']}. "
                f"Available: {product['quantity']}, "
                f"Required: {new_quantity}"
            )

        new_total = money(
            product["selling_price"] * new_quantity
        )

        new_gst, _, _ = calculate_gst(
            new_total,
            product["gst_rate"]
        )

        if existing:

            conn.execute("""
                UPDATE bill_items
                SET
                    quantity = ?,
                    price = ?,
                    total = ?,
                    hsn_code = ?,
                    gst_rate = ?,
                    gst_amount = ?
                WHERE id = ?
            """, (
                new_quantity,
                product["selling_price"],
                new_total,
                product["hsn_code"],
                product["gst_rate"],
                new_gst,
                existing["id"]
            ))

        else:

            conn.execute("""
                INSERT INTO bill_items
                (
                    bill_id,
                    product_name,
                    quantity,
                    price,
                    total,
                    hsn_code,
                    gst_rate,
                    gst_amount
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bill_id,
                product["name"],
                new_quantity,
                product["selling_price"],
                new_total,
                product["hsn_code"],
                product["gst_rate"],
                new_gst
            ))

        recalculate_bill(
            bill_id,
            conn
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def remove_bill_item(
    bill_id,
    product_name
):

    create_database()

    conn = get_connection()

    try:

        cursor = conn.execute("""
            DELETE FROM bill_items
            WHERE bill_id = ?
            AND LOWER(product_name) = LOWER(?)
        """, (
            bill_id,
            product_name.strip()
        ))

        if cursor.rowcount == 0:
            raise ValueError(
                f"'{product_name}' is not in bill {bill_id}."
            )

        recalculate_bill(
            bill_id,
            conn
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def recalculate_bill(
    bill_id,
    conn=None
):

    own_connection = False

    if conn is None:
        conn = get_connection()
        own_connection = True

    try:

        rows = conn.execute("""
            SELECT
                quantity,
                price,
                gst_rate
            FROM bill_items
            WHERE bill_id = ?
        """, (bill_id,)).fetchall()

        subtotal = 0
        total_gst = 0

        for row in rows:

            item_total = money(
                row["quantity"] * row["price"]
            )

            item_gst = money(
                item_total * row["gst_rate"] / 100
            )

            subtotal += item_total
            total_gst += item_gst

        subtotal = money(subtotal)
        total_gst = money(total_gst)

        cgst = money(total_gst / 2)
        sgst = money(total_gst - cgst)

        grand_total = money(
            subtotal + total_gst
        )

        conn.execute("""
            UPDATE bills
            SET
                subtotal = ?,
                gst_amount = ?,
                total_gst = ?,
                cgst = ?,
                sgst = ?,
                grand_total = ?
            WHERE id = ?
        """, (
            subtotal,
            total_gst,
            total_gst,
            cgst,
            sgst,
            grand_total,
            bill_id
        ))

        if own_connection:
            conn.commit()

        return {
            "subtotal": subtotal,
            "gst_amount": total_gst,
            "total_gst": total_gst,
            "cgst": cgst,
            "sgst": sgst,
            "grand_total": grand_total
        }

    finally:

        if own_connection:
            conn.close()


def get_bill_items(bill_id):

    create_database()

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM bill_items
        WHERE bill_id = ?
        ORDER BY id
    """, (bill_id,)).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


def get_bill_summary(bill_id):

    create_database()

    conn = get_connection()

    bill = conn.execute("""
        SELECT *
        FROM bills
        WHERE id = ?
    """, (bill_id,)).fetchone()

    if not bill:
        conn.close()
        return None

    items = conn.execute("""
        SELECT *
        FROM bill_items
        WHERE bill_id = ?
        ORDER BY id
    """, (bill_id,)).fetchall()

    conn.close()

    return {
        "bill": dict(bill),
        "items": [
            dict(item)
            for item in items
        ]
    }


# =========================================================
# FINALIZE BILL
# =========================================================

def finalize_bill(
    bill_id,
    payment_method="CASH",
    payment_reference=""
):

    create_database()

    payment_method = payment_method.upper().strip()

    if payment_method not in [
        "CASH",
        "UPI",
        "CARD"
    ]:
        raise ValueError(
            "Payment method must be CASH, UPI or CARD."
        )

    conn = get_connection()

    try:

        conn.execute("BEGIN IMMEDIATE")

        bill = conn.execute("""
            SELECT *
            FROM bills
            WHERE id = ?
        """, (bill_id,)).fetchone()

        if not bill:
            raise ValueError(
                f"Bill {bill_id} not found."
            )

        if bill["bill_type"] == "FINAL":

            items = conn.execute("""
                SELECT *
                FROM bill_items
                WHERE bill_id = ?
                ORDER BY id
            """, (bill_id,)).fetchall()

            return {
                "bill_id": bill_id,
                "subtotal": bill["subtotal"],
                "gst_amount": bill["gst_amount"],
                "total_gst": bill["total_gst"],
                "cgst": bill["cgst"],
                "sgst": bill["sgst"],
                "grand_total": bill["grand_total"],
                "payment_method": bill["payment_method"],
                "payment_reference": bill["payment_reference"],
                "items": [
                    dict(item)
                    for item in items
                ]
            }

        items = conn.execute("""
            SELECT *
            FROM bill_items
            WHERE bill_id = ?
            ORDER BY id
        """, (bill_id,)).fetchall()

        if not items:
            raise ValueError(
                "Cannot finalize an empty bill."
            )

        # ---------------------------------------------
        # VALIDATE STOCK FIRST
        # ---------------------------------------------

        products = []

        for item in items:

            product = conn.execute("""
                SELECT *
                FROM products
                WHERE LOWER(name) = LOWER(?)
            """, (item["product_name"],)).fetchone()

            if not product:
                raise ValueError(
                    f"Product '{item['product_name']}' no longer exists."
                )

            if product["quantity"] < item["quantity"]:
                raise ValueError(
                    f"Insufficient stock for {product['name']}. "
                    f"Available: {product['quantity']}, "
                    f"Required: {item['quantity']}"
                )

            if product["selling_price"] < product["cost_price"]:
                raise ValueError(
                    f"Sale blocked for {product['name']}."
                )

            products.append(product)

        # ---------------------------------------------
        # ATOMIC STOCK DECREMENT
        # ---------------------------------------------

        for item, product in zip(items, products):

            cursor = conn.execute("""
                UPDATE products
                SET quantity = quantity - ?
                WHERE id = ?
                AND quantity >= ?
            """, (
                item["quantity"],
                product["id"],
                item["quantity"]
            ))

            if cursor.rowcount != 1:
                raise ValueError(
                    f"Stock changed while finalizing "
                    f"{product['name']}."
                )

        # ---------------------------------------------
        # TOTALS
        # ---------------------------------------------

        subtotal = 0
        total_gst = 0

        for item in items:

            item_total = money(
                item["quantity"] * item["price"]
            )

            item_gst = money(
                item_total * item["gst_rate"] / 100
            )

            subtotal += item_total
            total_gst += item_gst

        subtotal = money(subtotal)
        total_gst = money(total_gst)

        cgst = money(total_gst / 2)
        sgst = money(total_gst - cgst)

        grand_total = money(
            subtotal + total_gst
        )

        # ---------------------------------------------
        # UPDATE BILL
        # ---------------------------------------------

        conn.execute("""
            UPDATE bills
            SET
                subtotal = ?,
                gst_amount = ?,
                total_gst = ?,
                cgst = ?,
                sgst = ?,
                grand_total = ?,
                payment_method = ?,
                payment_reference = ?,
                bill_type = 'FINAL'
            WHERE id = ?
        """, (
            subtotal,
            total_gst,
            total_gst,
            cgst,
            sgst,
            grand_total,
            payment_method,
            payment_reference,
            bill_id
        ))

        conn.commit()

        return {
            "bill_id": bill_id,
            "subtotal": subtotal,
            "gst_amount": total_gst,
            "total_gst": total_gst,
            "cgst": cgst,
            "sgst": sgst,
            "grand_total": grand_total,
            "payment_method": payment_method,
            "payment_reference": payment_reference,
            "items": [
                dict(item)
                for item in items
            ]
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================================================
# PAYMENT
# =========================================================

def update_bill_payment(
    bill_id,
    payment_method,
    payment_reference=""
):

    create_database()

    payment_method = payment_method.upper().strip()

    if payment_method not in [
        "CASH",
        "UPI",
        "CARD"
    ]:
        raise ValueError(
            "Payment method must be CASH, UPI or CARD."
        )

    conn = get_connection()

    cursor = conn.execute("""
        UPDATE bills
        SET
            payment_method = ?,
            payment_reference = ?
        WHERE id = ?
    """, (
        payment_method,
        payment_reference,
        bill_id
    ))

    if cursor.rowcount == 0:
        conn.close()
        raise ValueError(
            f"Bill {bill_id} not found."
        )

    conn.commit()
    conn.close()


# =========================================================
# SALES SUMMARY
# =========================================================

def get_sales_summary():

    create_database()

    conn = get_connection()

    row = conn.execute("""
        SELECT
            COUNT(*) AS total_bills,
            COALESCE(
                (
                    SELECT SUM(quantity)
                    FROM bill_items bi
                    JOIN bills b2
                    ON bi.bill_id = b2.id
                    WHERE b2.bill_type = 'FINAL'
                ),
                0
            ) AS items_sold,
            COALESCE(
                SUM(grand_total),
                0
            ) AS total_sales
        FROM bills
        WHERE bill_type = 'FINAL'
    """).fetchone()

    conn.close()

    return (
        f"Total Bills: {row['total_bills']}\n"
        f"Items Sold: {int(row['items_sold'])}\n"
        f"Total Sales: ₹{row['total_sales']:.2f}"
    )


# =========================================================
# DAILY CLOSE
# =========================================================

def get_daily_close():

    create_database()

    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()

    row = conn.execute("""
        SELECT
            COUNT(*) AS bills,
            COALESCE(SUM(subtotal), 0) AS subtotal,
            COALESCE(SUM(total_gst), 0) AS gst,
            COALESCE(SUM(cgst), 0) AS cgst,
            COALESCE(SUM(sgst), 0) AS sgst,
            COALESCE(SUM(grand_total), 0) AS grand_total
        FROM bills
        WHERE bill_type = 'FINAL'
        AND DATE(bill_date) = ?
    """, (today,)).fetchone()

    items = conn.execute("""
        SELECT
            COALESCE(SUM(bi.quantity), 0) AS items
        FROM bill_items bi
        JOIN bills b
        ON bi.bill_id = b.id
        WHERE b.bill_type = 'FINAL'
        AND DATE(b.bill_date) = ?
    """, (today,)).fetchone()

    payments = conn.execute("""
        SELECT
            payment_method,
            COUNT(*) AS bill_count,
            COALESCE(SUM(grand_total), 0) AS amount
        FROM bills
        WHERE bill_type = 'FINAL'
        AND DATE(bill_date) = ?
        GROUP BY payment_method
    """, (today,)).fetchall()

    top_items = conn.execute("""
        SELECT
            bi.product_name,
            SUM(bi.quantity) AS quantity
        FROM bill_items bi
        JOIN bills b
        ON bi.bill_id = b.id
        WHERE b.bill_type = 'FINAL'
        AND DATE(b.bill_date) = ?
        GROUP BY bi.product_name
        ORDER BY quantity DESC
        LIMIT 5
    """, (today,)).fetchall()

    conn.close()

    result = [
        "Daily Close",
        "-------------------",
        f"Date: {today}",
        f"Bills: {row['bills']}",
        f"Items Sold: {int(items['items'])}",
        f"Subtotal: ₹{row['subtotal']:.2f}",
        f"GST: ₹{row['gst']:.2f}",
        f"CGST: ₹{row['cgst']:.2f}",
        f"SGST: ₹{row['sgst']:.2f}",
        f"Grand Total: ₹{row['grand_total']:.2f}",
        "",
        "Payment Breakdown"
    ]

    for payment in payments:
        result.append(
            f"{payment['payment_method']}: "
            f"{payment['bill_count']} bills - "
            f"₹{payment['amount']:.2f}"
        )

    result.append("")
    result.append("Top Items")

    if top_items:
        for item in top_items:
            result.append(
                f"{item['product_name']}: "
                f"{int(item['quantity'])}"
            )
    else:
        result.append("No sales today.")

    return "\n".join(result)


# =========================================================
# ALL BILLS
# =========================================================

def get_all_bills():

    create_database()

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM bills
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# START DATABASE
# =========================================================

create_database()