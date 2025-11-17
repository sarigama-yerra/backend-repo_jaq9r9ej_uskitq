import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import db, create_document, get_documents
from schemas import Product

app = FastAPI(title="Clothing Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Clothing Store Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# Seed some default products for shirts and pants if collection empty
@app.post("/seed", tags=["dev"]) 
def seed_products():
    try:
        existing = get_documents("product", {}, limit=1)
        if existing:
            return {"status": "ok", "message": "Products already seeded"}
    except Exception:
        # If database isn't available, return message
        raise HTTPException(status_code=500, detail="Database not available to seed products")

    sample_products = [
        Product(title="Classic White Tee", description="Premium cotton crew neck t‑shirt.", price=19.99, category="shirt", in_stock=True, image_url="https://images.unsplash.com/photo-1523381294911-8d3cead13475?w=800&q=80", sizes=["S","M","L","XL"], rating=4.6),
        Product(title="Relaxed Black Tee", description="Soft, breathable everyday t‑shirt.", price=17.50, category="shirt", in_stock=True, image_url="https://images.unsplash.com/photo-1602810318383-8de9f1a2cd3f?w=800&q=80", sizes=["S","M","L"], rating=4.4),
        Product(title="Slim Fit Chinos", description="Tapered stretch chinos for all‑day comfort.", price=39.00, category="pants", in_stock=True, image_url="https://images.unsplash.com/photo-1603252109303-2751441dd157?w=800&q=80", sizes=["28","30","32","34","36"], rating=4.7),
        Product(title="Everyday Jeans", description="Medium wash denim with a classic fit.", price=45.00, category="pants", in_stock=True, image_url="https://images.unsplash.com/photo-1542272201-b1ca555f8505?w=800&q=80", sizes=["28","30","32","34","36","38"], rating=4.5),
    ]

    inserted = []
    for p in sample_products:
        inserted_id = create_document("product", p)
        inserted.append(inserted_id)

    return {"status": "ok", "inserted": inserted}

class ProductFilters(BaseModel):
    category: Optional[str] = None  # "shirt" or "pants"
    search: Optional[str] = None

@app.get("/products", response_model=List[dict])
def list_products(category: Optional[str] = None, search: Optional[str] = None, limit: int = 50):
    try:
        query = {}
        if category:
            query["category"] = category
        if search:
            query["title"] = {"$regex": search, "$options": "i"}
        docs = get_documents("product", query, limit=limit)
        # Convert ObjectId to string for frontend
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
