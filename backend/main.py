# main.py
# # FastAPI + Uvicorn: Core Concept Notes
# 
# - **Visitor**  
#   - You (or any client) sending a request.  
#   - Example: typing a URL in Chrome or using Postman.
# 
# - **Browser**  
#   - Vehicle for the visitor.  
#   - Wraps the request into HTTP format and sends it to the server.  
#   - Examples: Chrome, Firefox, Edge.
# 
# - **Computer / Server**  
#   - The building that hosts programs.  
#   - Has an IP address = building address.
# 
# - **Port**  
#   - Apartment number inside the building.  
#   - Allows multiple programs to run independently.  
#   - Example ports: 8000 (FastAPI), 3000 (React dev server), 3306 (MySQL).
# 
# - **Uvicorn (Web Server Software)**  
#   - Waiter standing at the apartment door (port).  
#   - Listens for incoming requests.  
#   - Forwards requests to FastAPI (chef).  
#   - Returns the response back to the visitor.
# 
# - **FastAPI (Web Framework) rules + structure + logic helpers.**  
#   - Chef living inside the apartment.  
#   - Runs application logic (routes, functions).  
#   - Prepares the response depending on the request.  
#   - Does NOT listen to ports — relies on Uvicorn.
# 
# - **Request Flow (Visitor → Server → Response)**  
#   1. Visitor sends request via browser.  
#   2. Request arrives at the server IP + port (apartment door).  
#   3. Uvicorn (waiter) catches the request.  
#   4. FastAPI (chef) runs the logic and prepares the response.  
#   5. Uvicorn returns the response to the visitor via the browser.  
# 
# - **Example Routes**  
#   - `/` → returns a welcome message.  
#   - `/users/{id}` → returns user info based on the ID.
# 
# - **Key Concept**  
#   - Server (Uvicorn) = opens port, listens, delivers requests.  
#   - Framework (FastAPI) = defines what to do with requests.  
#   - Port = numbered door to the program.  
#   - Visitor = triggers the request.  
#   - Browser = sends the request in proper format.
# 
# - **Visual Analogy**  
# Visitor (You) → Browser → Building (Server/IP) → Apartment (Port) → Waiter (Uvicorn) → Chef (FastAPI) → Response back

from typing import Optional
from fastapi import Query
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import ProductCreate, ProductResponse,ProductUpdate
from database import SessionLocal, engine
import database_model
from sqlalchemy.orm import Session
from sqlalchemy import func
from groq import Groq
from dotenv import load_dotenv
import os
from fastapi.responses import StreamingResponse

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

# Base is the parent class that all SQLAlchemy models inherit from.
# When a class inherits from Base, it gets registered as a database table.
# Example: class Product(Base) → Product becomes a table definition.

# Base.metadata contains all registered table definitions
# (table names, columns, types, primary keys, etc.)

# create_all() reads everything stored in Base.metadata
# and creates those tables in the actual database if they don't exist.

# bind=engine tells SQLAlchemy which database connection to use
# to execute the CREATE TABLE commands.

database_model.Base.metadata.create_all(bind=engine)

# How this works: 
# You (visitor) → Browser → Building (Server) → Apartment 8000 (Port) → 
# Uvicorn (Waiter) → FastAPI (Chef + recipe for "/") → Cooked response → 
# Waiter → Browser → You see "Hello world"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Important

# -----------------------------
# 4️⃣ Flow for GET (Read Product)
# -----------------------------
# Step 1: Fetch SQLAlchemy object from DB
# Step 2: Convert DB object → Pydantic ProductResponse
# Step 3: Return JSON to client

#@app.get("/products", response_model=list[ProductResponse])
#def get_all_products(db: Session = Depends(get_db)):
#    db_products = db.query(database_model.Product).all()
#    if db_products:
#       return db_products
#    else:
#        raise HTTPException(status_code=404, detail="Database is Empty")


# How this works
# You (visitor) → Browser/Postman → Building (Server) → Apartment 8000 (Port) → 
# Uvicorn (Waiter) → FastAPI (Chef + recipe for "/product/{ID}") → 
# Chef checks storage room (products list) → Finds box with matching ID → Cooked response → 
# Waiter → Browser → You see product JSON or "product not found"


# How this works:
# You (visitor) → Browser/Postman → Building (Server) → Apartment 8000 (Port) →
# Uvicorn (Waiter) → FastAPI (Chef + recipe for "/product" POST) →
# Chef receives new box (product from request body) → Puts it into storage room (products list) →
# Chef wraps it nicely (returns the Product object) → Waiter delivers back → Browser → You see the new product JSON


# Important: 
# -----------------------------
# 3️⃣ Flow for POST (Create Product)
# -----------------------------
# Step 1: FastAPI receives request body → Pydantic ProductCreate
# Step 2: Convert ProductCreate → SQLAlchemy Product row
# Step 3: Add row to DB and commit
# Step 4: Return response (optional: Pydantic ProductResponse)


@app.get("/products/low_stock", response_model=list[ProductResponse])
def low_stock_products( threshold: int 
                       = Query(5, description="Max quantity to consider low stock"),
                         db: Session = Depends(get_db) ): 
    products = db.query(database_model.Product).filter(database_model.Product.quantity <= threshold).all()
    return products

# ---------------------------------------------------------
# Bulk insert products
# ---------------------------------------------------------
@app.post("/products/bulk", response_model=list[ProductResponse])
def bulk_create_products(products: list[ProductCreate], db: Session = Depends(get_db)):
    db_products = []

    for product in products:
        # Convert Pydantic → SQLAlchemy
        db_product = database_model.Product(**product.dict())
        db.add(db_product)      # Add to session
        db_products.append(db_product)

    db.commit()                 # Single commit for all products
    for product in db_products:
        db.refresh(product)      # Refresh to get IDs and DB defaults

    return db_products


# ---------------------------------------------------------
# Bulk delete by SKU list
# ---------------------------------------------------------
@app.delete("/products/bulk")
def bulk_delete(
    category: Optional[str] = None,  # Optional filter: delete products of a specific category
    max_price: Optional[float] = None,  # Optional filter: delete products with price <= max_price
    min_price: Optional[float] = None,  # Optional filter: delete products with price >= min_price
    db: Session = Depends(get_db)  # Database session injected by FastAPI
):
    # Start a query on the Product table
    query = db.query(database_model.Product)

    # Apply category filter if provided
    if category:
        category = category.strip()

        query = query.filter(database_model.Product.category == category)

    # Apply maximum price filter if provided
    if max_price is not None:
        query = query.filter(database_model.Product.price <= max_price)

    # Apply minimum price filter if provided
    if min_price is not None:
        query = query.filter(database_model.Product.price >= min_price)

    # Perform bulk delete on all rows that match the query
    count = query.delete(synchronize_session=False)  # Set False for efficiency, skip session sync

    # Commit the deletion to the database
    db.commit()

    # Return how many products were deleted
    return {"deleted_count": count}


# ---------------------------------------------------------
# Get a single product by SKU
# ---------------------------------------------------------
@app.get("/products/{sku}", response_model=ProductResponse)
def get_product(sku: str, db: Session = Depends(get_db)):
    # Query DB: filter by SKU, fetch first matching row
    product = db.query(database_model.Product).filter(database_model.Product.sku == sku).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ---------------------------------------------------------
# Create a single product
# ---------------------------------------------------------
@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Convert Pydantic model → dict → SQLAlchemy object
    db_product = database_model.Product(**product.dict())
    
    db.add(db_product)  # Add object to session (not yet in DB)
    db.commit()         # Commit session → INSERT into DB
    db.refresh(db_product)  # Reload object from DB to get autogenerated fields (like ID)
    return db_product


# ---------------------------------------------------------
# Update full product
# ---------------------------------------------------------
@app.put("/products/{sku}", response_model=ProductResponse)
def update_product(sku: str, product: ProductCreate, db: Session = Depends(get_db)):
    # Fetch existing product from DB
    db_product = db.query(database_model.Product).filter(database_model.Product.sku == sku).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update fields one by one using setattr (Python reflection)
    for key, value in product.dict().items():
        setattr(db_product, key, value)

    db.commit()         # Persist changes to DB
    db.refresh(db_product)  # Refresh object with new DB state
    return db_product

# ---------------------------------------------------------
# Partial update
# ---------------------------------------------------------
@app.patch("/products/{sku}", response_model=ProductResponse)
def partial_update_product(sku: str, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(database_model.Product).filter(database_model.Product.sku == sku).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Only include fields provided (exclude unset) → prevents overwriting
    update_data = product.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product


# ---------------------------------------------------------
# Delete single product
# ---------------------------------------------------------
@app.delete("/products/{sku}")
def delete_product(sku: str, db: Session = Depends(get_db)):
    db_product = db.query(database_model.Product).filter(database_model.Product.sku == sku).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)  # Remove object from DB
    db.commit()            # Commit DELETE
    return {"message": "Product deleted successfully"}


# ---------------------------------------------------------
# Get products with filtering, sorting and pagination
# ---------------------------------------------------------
@app.get("/products", response_model=list[ProductResponse])
def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort: Optional[str] = None,
    max_items: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(database_model.Product)  # Start query for Product table

    # --- Filters ---
    if category:
        query = query.filter(database_model.Product.category == category)  # SQL WHERE category=?
    if search:
        query = query.filter(database_model.Product.name.ilike(f"%{search}%"))  # SQL ILIKE for partial match
    if min_price is not None:
        query = query.filter(database_model.Product.price >= min_price)  # SQL WHERE price >= ?
    if max_price is not None:
        query = query.filter(database_model.Product.price <= max_price)  # SQL WHERE price <= ?

    # --- Sorting ---
    if sort == "price_asc":
        query = query.order_by(database_model.Product.price.asc())  # SQL ORDER BY price ASC
    elif sort == "price_desc":
        query = query.order_by(database_model.Product.price.desc())  # SQL ORDER BY price DESC
    elif sort == "name_asc":
        query = query.order_by(database_model.Product.name.asc())  # ORDER BY name ASC
    elif sort == "name_desc":
        query = query.order_by(database_model.Product.name.desc())  # ORDER BY name DESC

    # --- Pagination ---
    # OFFSET skip → skip first N rows
    # LIMIT max_items → take max N rows
    if max_items is not None:
        query = query.limit(max_items)
    if skip is not None:
         query = query.offset(skip)
    products = query.all()
    return products  # Execute query and return list of SQLAlchemy objects



# ---------------------------------------------------------
# Categories summary stats
# ---------------------------------------------------------
@app.get("/stats/categories-summary")
def categories_summary(db: Session = Depends(get_db)):
    # Aggregate query: sum price*quantity and quantity per category
    query = (
        db.query(
            database_model.Product.category,
            func.sum(database_model.Product.price * database_model.Product.quantity).label("total_price"),
            func.sum(database_model.Product.quantity).label("total_quantity")
        )
        .group_by(database_model.Product.category)  # GROUP BY category
    )

    results = query.all()  # List of tuples: [(category, total_price, total_quantity), ...]

    # Build dict per category
    per_category_summary = {
        category: {"total_price": total_price, "total_quantity": total_quantity}
        for category, total_price, total_quantity in results
    }

    # Grand totals across all categories
    grand_total_price = sum(item["total_price"] for item in per_category_summary.values())
    grand_total_quantity = sum(item["total_quantity"] for item in per_category_summary.values())

    return {
        "per_category_summary": per_category_summary,
        "grand_totals": {"total_price": grand_total_price, "total_quantity": grand_total_quantity}
    }

@app.post("/ai/chat")
def chat(question: str, db: Session = Depends(get_db)):
    products = db.query(database_model.Product).all()
    low_stock = db.query(database_model.Product).filter(database_model.Product.quantity <= 5).all()

    products_data = [
        {"sku": p.sku, "name": p.name, "category": p.category, "price": p.price, "quantity": p.quantity}
        for p in products
    ]
    low_stock_data = [
        {"sku": p.sku, "name": p.name, "quantity": p.quantity}
        for p in low_stock
    ]

    prompt = """You are an inventory assistant. 
    Answer ONLY the user's specific question using the provided inventory data.
    Low stock threshold is 5 units unless user specifies otherwise.
    Do not generate reports unless explicitly asked.
    Be concise and direct."""

    def stream_response():
        stream = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Products: {products_data}\nLow Stock: {low_stock_data}\nQuestion: {question}"}
            ],
            reasoning_format="hidden",
            stream=True   # 👈 only change here
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return StreamingResponse(stream_response(), media_type="text/plain")