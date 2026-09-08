# 🛒 Supermarket Ops Agent

A Telegram-based intelligent operations management system designed for Indian kirana stores and supermarkets.

The system helps manage **inventory, sales, billing, customer credit, payments, daily reports, invoices, and weekly sales analysis** through a conversational Telegram interface.

---

## 🚀 Features

### 📦 Inventory Management

* Add new products
* Receive stock
* Check current stock
* View product details
* Identify low-stock products
* Track cost price and selling price
* Prevent selling below cost price
* Prevent selling more stock than available

### 🧾 Billing & Sales

* Create multi-item bills
* Add and remove items before finalization
* View bill before finalizing
* Finalize sales through Telegram
* Support payment modes:

  * Cash
  * UPI
  * Card
* Generate PDF invoices

### 💰 Customer Khata

* Add customer credit
* Record customer payments
* Check outstanding balance
* View payment history

### 📊 Reports & Analytics

* Daily sales summary
* Daily closing report
* GST summary
* Top-selling products
* Low-stock alerts
* Weekly sales analysis
* Automatic PPTX report generation with charts and insights

### 🤖 AI Agent

The system includes an AI-powered conversational agent that can understand incomplete requests and ask for the required information.

For example:

```text
User: Add a new product called Biscuit

Agent: What is the cost price?

User: 10

Agent: What is the selling price?

User: 15

Agent: What is the quantity?

User: 20

Agent: Product added successfully.
```

The agent collects the required information before executing inventory actions.

---

## 🏗️ Technology Stack

* **Python**
* **SQLite**
* **Telegram Bot API**
* **python-telegram-bot**
* **Ollama**
* **Llama 3.2**
* **ReportLab** – PDF invoice generation
* **python-pptx** – Weekly sales presentation
* **Matplotlib** – Charts and visualization
* **python-dotenv**
* **Git / GitHub**

---

## 📁 Project Structure

```text
supermarket_ops_agent/
│
├── agent.py
├── agent_tools.py
├── bot_final.py
├── database.py
├── bot_ai_database.py
├── customer_account.py
├── invoice.py
├── sales_report.py
├── weekly_analysis.py
│
├── supermarket.db
├── weekly_sales_analysis.pptx
├── daily_sales_report.pdf
│
├── .env
├── README.md
└── venv/
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd supermarket_ops_agent
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

### Windows

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install python-telegram-bot python-dotenv reportlab pillow charset-normalizer python-pptx matplotlib
```

### 5. Configure environment variables

Create a `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Do **not** commit the `.env` file or expose the Telegram bot token publicly.

---

## 🤖 Ollama Setup

Install Ollama and download the required model:

```bash
ollama pull llama3.2
```

Check the installation:

```bash
ollama --version
```

Start Ollama and make sure the model is available before running the agent.

---

## ▶️ Run the Bot

Activate the virtual environment:

```bash
venv\Scripts\activate
```

Run:

```bash
python bot_final.py
```

Then open the Telegram bot and start interacting with it.

---

## 💬 Example Commands

### Inventory

```text
/stock Maggi
```

```text
/addproduct Milk 25 30 50
```

```text
/receive Maggi 50 12 14
```

```text
/lowstock
```

### Billing

```text
/bill
```

```text
/additem Maggi 2
```

```text
/additem Milk 1
```

```text
/viewbill
```

```text
/finalize Cash
```

### Customer Accounts

```text
/credit Ramesh 500
```

```text
/payment Ramesh 300
```

```text
/balance Ramesh
```

```text
/payments Ramesh
```

### Reports

```text
/sales
```

```text
/dailyclose
```

---

## 🧾 PDF Invoice

After finalizing a bill, the system generates a PDF invoice containing the sale details.

The invoice can be used as a customer bill/receipt.

---

## 📊 Weekly Sales Analysis

The system can generate:

```text
weekly_sales_analysis.pptx
```

The presentation contains:

* Sales summary
* Top-selling products
* Product sales details
* Stock health
* Low-stock alerts
* Business insights
* Charts and visualizations

---

## 🔐 Business Rules & Guardrails

The system implements important business validations:

* Selling price cannot be lower than cost price
* Stock cannot become negative
* Overselling is prevented
* Invalid quantities are rejected
* Invalid prices are rejected
* Customer payments are validated
* Inventory actions are executed only after required information is collected

---

## 💾 Data Persistence

The application uses **SQLite** for persistent storage.

The database stores information related to:

* Products
* Inventory
* Bills
* Bill items
* GST information
* Customer accounts
* Payment history

Data remains available after restarting the application.

---

## 🎯 Project Objective

The objective of the Supermarket Ops Agent is to provide a simple conversational interface for supermarket operations.

Instead of navigating multiple screens, the store operator can interact with the system through Telegram and perform common business operations using natural language or commands.

---

## 👨‍💻 Project Status

**Status: Working Prototype**

Implemented modules include:

* Inventory management
* Stock receiving
* Sales
* Multi-item billing
* GST handling
* Customer credit
* Payments
* Daily closing
* PDF invoice generation
* Weekly sales analysis
* AI-assisted conversational interaction

---

## 📌 Future Improvements

* PostgreSQL support for production deployment
* Improved transaction-level bill architecture
* Stronger multi-user concurrency handling
* Complete weekly date-based filtering
* Advanced GST validation
* Payment reconciliation
* Persistent conversational memory
* Cloud deployment
* Automated backup and recovery

---

## 📜 License

This project is developed as an academic / take-home project.
