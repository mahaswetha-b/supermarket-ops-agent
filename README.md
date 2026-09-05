# Supermarket Operations Management Agent

A Telegram-based intelligent operations management system designed to streamline supermarket inventory, sales, customer accounts, invoicing, and reporting.

## Project Overview

The Supermarket Operations Management Agent provides a centralized interface for managing essential supermarket operations through Telegram.

The system combines a structured SQLite database with a locally hosted AI model to support both operational commands and natural-language queries. It enables users to monitor inventory, process sales, manage customer balances, generate invoices, and obtain daily sales summaries through a simple conversational interface.

## Key Features

- **Inventory Management** – Add products, update stock quantities, and check product availability.
- **Sales Management** – Process product sales and automatically update inventory.
- **Low-Stock Monitoring** – Identify products that require restocking.
- **Customer Account Management** – Maintain customer credit, payments, and outstanding balances.
- **Invoice Generation** – Automatically generate PDF invoices for completed sales.
- **Sales Reporting** – Generate daily sales reports in PDF format.
- **Natural-Language Queries** – Retrieve supermarket information using conversational queries.
- **Local AI Integration** – Use a locally hosted Llama 3.2 model through Ollama for AI-based responses.
- **Telegram Interface** – Perform operations through simple Telegram commands.

## System Architecture

```text
                 ┌─────────────────────┐
                 │   Telegram User     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Telegram Bot      │
                 │   Application       │
                 └───────┬─────┬───────┘
                         │     │
             ┌───────────┘     └────────────┐
             ▼                              ▼
   ┌──────────────────┐           ┌──────────────────┐
   │ SQLite Database  │           │   Local AI       │
   │                  │           │   Ollama         │
   │ • Products       │           │   Llama 3.2      │
   │ • Sales          │           └──────────────────┘
   │ • Customers      │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ PDF Generation   │
   │                  │
   │ • Invoices       │
   │ • Sales Reports  │
   └──────────────────┘
