import sqlite3


# =========================
# CREATE DATABASE
# =========================

def create_database():

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            quantity INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================
# ADD PRODUCT
# =========================

def add_product(name, cost_price, selling_price, quantity):

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, quantity
        FROM products
        WHERE LOWER(name) = LOWER(?)
    """, (name,))

    product = cursor.fetchone()

    if product:

        product_id, old_quantity = product

        new_quantity = old_quantity + quantity

        cursor.execute("""
            UPDATE products
            SET cost_price = ?,
                selling_price = ?,
                quantity = ?
            WHERE id = ?
        """, (
            cost_price,
            selling_price,
            new_quantity,
            product_id
        ))

    else:

        cursor.execute("""
            INSERT INTO products
            (name, cost_price, selling_price, quantity)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            cost_price,
            selling_price,
            quantity
        ))

    conn.commit()
    conn.close()


# =========================
# GET STOCK
# =========================

def get_stock(product_name):

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT SUM(quantity)
        FROM products
        WHERE LOWER(name) = LOWER(?)
    """, (product_name,))

    product = cursor.fetchone()

    conn.close()

    if product is None or product[0] is None:
        return None

    return product[0]


# =========================
# SELL PRODUCT
# =========================

def sell_product(product_name, quantity):

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            name,
            selling_price,
            SUM(quantity)
        FROM products
        WHERE LOWER(name) = LOWER(?)
        GROUP BY LOWER(name)
    """, (product_name,))

    product = cursor.fetchone()

    if not product:

        conn.close()

        return None

    name, price, stock = product

    if quantity <= 0:

        conn.close()

        return None

    if quantity > stock:

        conn.close()

        return None

    total = price * quantity

    remaining_to_remove = quantity

    cursor.execute("""
        SELECT id, quantity
        FROM products
        WHERE LOWER(name) = LOWER(?)
        ORDER BY id
    """, (product_name,))

    rows = cursor.fetchall()

    for product_id, current_quantity in rows:

        if remaining_to_remove <= 0:
            break

        if current_quantity >= remaining_to_remove:

            new_quantity = (
                current_quantity - remaining_to_remove
            )

            cursor.execute("""
                UPDATE products
                SET quantity = ?
                WHERE id = ?
            """, (
                new_quantity,
                product_id
            ))

            remaining_to_remove = 0

        else:

            cursor.execute("""
                UPDATE products
                SET quantity = 0
                WHERE id = ?
            """, (product_id,))

            remaining_to_remove -= current_quantity

    # Create bill
    cursor.execute("""
        INSERT INTO bills
        (product_name, quantity, price, total)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        quantity,
        price,
        total
    ))

    conn.commit()
    conn.close()

    return price


# =========================
# LOW STOCK
# =========================

def get_low_stock(limit=10):

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            name,
            SUM(quantity) AS total_quantity
        FROM products
        GROUP BY LOWER(name)
        HAVING total_quantity <= ?
        ORDER BY total_quantity
    """, (limit,))

    products = cursor.fetchall()

    conn.close()

    return products


# =========================
# ALL PRODUCTS
# =========================

def get_all_products():

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            name,
            SUM(quantity) AS total_quantity
        FROM products
        GROUP BY LOWER(name)
        ORDER BY LOWER(name)
    """)

    products = cursor.fetchall()

    conn.close()

    return products


# =========================
# ALL BILLS
# =========================

def get_all_bills():

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            product_name,
            quantity,
            price,
            total
        FROM bills
        ORDER BY id DESC
    """)

    bills = cursor.fetchall()

    conn.close()

    return bills


# =========================
# SALES SUMMARY
# =========================

def get_sales_summary():

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(quantity), 0),
            COALESCE(SUM(total), 0)
        FROM bills
    """)

    summary = cursor.fetchone()

    conn.close()

    return summary


# =========================
# MAIN TEST
# =========================

if __name__ == "__main__":

    create_database()

    summary = get_sales_summary()

    print("Daily Sales Summary")
    print("-------------------")
    print(f"Total Bills: {summary[0]}")
    print(f"Items Sold: {summary[1]}")
    print(f"Total Sales: ₹{summary[2]}")