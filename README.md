# 📦 Simple Inventory Management System

A full-stack inventory management application built with **FastAPI** and **Streamlit**. Supports full CRUD operations, product filtering, low-stock alerts, category analytics, CSV export, and an AI-powered chat assistant that answers natural language questions about your inventory.

---

## ✨ Features

- **Product Management** — Create, read, update, and delete products
- **Bulk Operations** — Insert or delete multiple products in a single request
- **Search & Filter** — Filter by category, name, price range, with sorting and pagination
- **Low Stock Alerts** — Configurable threshold monitor that auto-highlights critical items
- **Analytics Charts** — Category-wise inventory quantity and value visualizations
- **AI Chat Assistant** — Ask natural language questions about your inventory (powered by Groq)
- **CSV Export** — Download full inventory as a CSV file
- **Interactive Table** — AG Grid table with single-row selection for update/delete actions

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit, AG Grid, Plotly |
| Backend | FastAPI, Uvicorn |
| Database | SQLite, SQLAlchemy ORM |
| AI | Groq API (Qwen 32B) |
| Data Validation | Pydantic |

---

## 📁 Project Structure

```
Simple-Inventory-Management-System/
│
├── backend/
│   ├── main.py               # FastAPI app — all API routes and endpoints
│   ├── database.py           # SQLAlchemy engine and session setup
│   ├── database_model.py     # SQLAlchemy Product table model
│   └── models.py             # Pydantic schemas (request/response validation)
│
├── frontend/
│   ├── app.py                # Streamlit frontend
│   └── styles.py             # Custom CSS injection and UI helpers
│
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not committed)
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/m-noumanfazil/Simple-Inventory-Management-System.git
cd Simple-Inventory-Management-System
```

### 2. Create and activate a virtual environment

```bash
python -m venv env

# Windows
env\Scripts\activate

# Mac/Linux
source env/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root folder:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com)

### 5. Run the FastAPI backend

```bash
uvicorn main:app --reload
```

Backend will be running at `http://127.0.0.1:8000`  
Interactive API docs available at `http://127.0.0.1:8000/docs`

### 6. Run the Streamlit frontend

Open a second terminal (with the virtual environment activated):

```bash
streamlit run app.py
```

Frontend will be running at `http://localhost:8501`

---

## 🔌 API Endpoints

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/products` | Get all products (supports filters, sort, pagination) |
| `GET` | `/products/{sku}` | Get a single product by SKU |
| `POST` | `/products` | Create a single product |
| `PUT` | `/products/{sku}` | Full update of a product |
| `PATCH` | `/products/{sku}` | Partial update of a product |
| `DELETE` | `/products/{sku}` | Delete a single product |
| `GET` | `/products/low_stock` | Get products below stock threshold |
| `POST` | `/products/bulk` | Bulk create products |
| `DELETE` | `/products/bulk` | Bulk delete by category or price range |

### Stats & AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/stats/categories-summary` | Aggregated quantity and value per category |
| `POST` | `/ai/chat` | Streaming AI chat about inventory data |

### Query Parameters for `GET /products`

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category |
| `search` | string | Search by product name (partial match) |
| `min_price` | float | Minimum price filter |
| `max_price` | float | Maximum price filter |
| `sort` | string | `price_asc`, `price_desc`, `name_asc`, `name_desc` |
| `max_items` | int | Limit number of results (default: 50) |
| `skip` | int | Offset for pagination (default: 0) |

---
