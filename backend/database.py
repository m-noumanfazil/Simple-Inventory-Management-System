# database.py
# -------------------------
# This file sets up the "plumbing" for your database.
# Think of it as the Storage Room Manager:
# - Engine = the smart door to your storage room (DB)
# - SessionLocal = temporary keys for chefs (FastAPI routes)
# - Base = blueprints for shelves (tables)

from sqlalchemy import create_engine        # Engine = door to the storage room
from sqlalchemy.ext.declarative import declarative_base  # Base = blueprint for shelves (tables)
from sqlalchemy.orm import sessionmaker     # SessionLocal = factory for temporary keys

# -------------------------
# 1️⃣ Where the database lives
# -------------------------
# SQLALCHEMY_DATABASE_URL = path to your DB file
# SQLite: simple file-based DB
# Postgres/MySQL: full server-based DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# sqlite:///./test.db
#   └── ./test.db = relative path (current folder)
#   └── sqlite:/// = SQLite protocol
# For Postgres: "postgresql://user:password@localhost/dbname"

# -------------------------
# 2️⃣ Engine = Smart Door
# -------------------------
# The engine is the "door to the storage room".
# It knows how to talk to the database and execute SQL commands.
# connect_args={"check_same_thread": False} → allows multiple chefs (threads) to use the same door
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite is picky; threads need permission
)

# -------------------------
# 3️⃣ SessionLocal = Factory for Temporary Keys
# -------------------------
# Each time a FastAPI route wants to touch the DB:
# 1. It asks SessionLocal for a key
# 2. Uses it to read/write boxes (data)
# 3. Returns the key
# These keys only exist while the request is running.
SessionLocal = sessionmaker(
    autocommit=False,   # chef must explicitly save changes (db.commit())
    autoflush=False,    # chef controls when the changes are pushed to DB
    bind=engine         # which door (engine) this key opens
)



# -------------------------
# 5️⃣ Usage Analogy
# -------------------------
# Visitor (browser) → Uvicorn → FastAPI route (chef) →
# asks for a Session (key) → Engine (door) → Storage Room (DB file) →
# Chef moves boxes (CRUD) → Session closes key → Response back

# Example usage in a route:
# db = SessionLocal()      # get key
# db.add(product)          # put box on shelf
# db.commit()              # save permanently
# db.refresh(product)      # get latest info
# db.close()               # return key