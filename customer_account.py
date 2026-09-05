import sqlite3


# =========================
# CREATE CUSTOMER TABLE
# =========================

def create_customer_table():

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            balance REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# =========================
# ADD CREDIT
# =========================

def add_credit(customer_name, amount):

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, balance FROM customers WHERE LOWER(name) = LOWER(?)",
        (customer_name,)
    )

    customer = cursor.fetchone()

    if customer:

        new_balance = customer[1] + amount

        cursor.execute(
            "UPDATE customers SET balance = ? WHERE id = ?",
            (new_balance, customer[0])
        )

    else:

        cursor.execute(
            "INSERT INTO customers (name, balance) VALUES (?, ?)",
            (customer_name, amount)
        )

        new_balance = amount

    conn.commit()
    conn.close()

    return new_balance


# =========================
# MAKE PAYMENT
# =========================

def make_payment(customer_name, amount):

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, balance FROM customers WHERE LOWER(name) = LOWER(?)",
        (customer_name,)
    )

    customer = cursor.fetchone()

    # Customer not found
    if not customer:

        conn.close()

        return None


    current_balance = customer[1]

    # Payment cannot be negative
    if amount <= 0:

        conn.close()

        return None


    # Calculate remaining balance
    new_balance = current_balance - amount


    # Balance should not go below zero
    if new_balance < 0:

        new_balance = 0


    cursor.execute(
        "UPDATE customers SET balance = ? WHERE id = ?",
        (new_balance, customer[0])
    )

    conn.commit()
    conn.close()

    return new_balance


# =========================
# GET BALANCE
# =========================

def get_balance(customer_name):

    conn = sqlite3.connect("supermarket.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name, balance
        FROM customers
        WHERE LOWER(name) = LOWER(?)
        """,
        (customer_name,)
    )

    customer = cursor.fetchone()

    conn.close()

    if not customer:

        return None


    return customer[1]


# =========================
# TEST
# =========================

if __name__ == "__main__":

    create_customer_table()


    # Add credit
    balance = add_credit(
        "Ramesh",
        500
    )

    print(
        f"Ramesh credit: ₹{balance}"
    )


    # Make payment
    balance = make_payment(
        "Ramesh",
        300
    )

    print(
        f"Ramesh remaining balance: ₹{balance}"
    )


    # Get balance
    balance = get_balance(
        "Ramesh"
    )

    if balance is not None:

        print(
            f"Customer: Ramesh"
        )

        print(
            f"Balance: ₹{balance}"
        )

    else:

        print(
            "Customer not found."
        )