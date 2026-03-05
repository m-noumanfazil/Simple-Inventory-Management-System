#models.py
from pydantic import BaseModel, Field, validator
from typing import  Optional
# -----------------------------
# 1️⃣ Pydantic Classes (API layer)
# -----------------------------
# ProductCreate = input schema for creating/updating product
# ProductResponse = output schema for sending product info to client
#   - orm_mode=True allows reading attributes from SQLAlchemy objects
class ProductCreate(BaseModel):
    category: str
    sku: str = Field(..., min_length=3, max_length=20)  # shop-owner-friendly code
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)

    @validator("category")
    def category_must_be_valid(cls, v):
        valid_categories = ["vegetables", "fruits", "electronics", "confectionaries"]
        if v.lower() not in valid_categories:
            raise ValueError(f"Category must be one of {valid_categories}")
        return v.lower()



class ProductResponse(BaseModel):
    id: int
    category: str
    sku: str
    name: str
    description: str
    price: float        # no gt=0 restriction
    quantity: int

    class Config:
        orm_mode = True

        
class ProductUpdate(BaseModel): # for the Patch api call
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None



