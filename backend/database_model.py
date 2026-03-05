# database_model.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

# Create a base class for all database models (table blueprints)
# Any class that inherits from Base becomes a table in the database
Base = declarative_base()

class Product(Base):  
    # Inheriting from Base tells SQLAlchemy:
    # "This class should be mapped to a database table"
    
    __tablename__ = "product"  # Name of the table in the database

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)
    sku = Column(String, unique=True, index=True)       # unique code for shop owner
    name = Column(String)
    description = Column(String)
    price = Column(Float)
    quantity = Column(Integer)