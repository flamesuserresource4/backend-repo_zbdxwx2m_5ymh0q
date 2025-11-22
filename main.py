import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Order

app = FastAPI(title="Flamesblue API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = {**doc}
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    # Convert datetimes to isoformat strings
    for k, v in list(out.items()):
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
    return out


@app.get("/")
def read_root():
    return {"message": "Flamesblue backend is running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
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


# Orders API
@app.get("/api/orders")
def list_orders(limit: Optional[int] = 50):
    docs = get_documents("order", {}, limit=limit)
    return [serialize_doc(d) for d in docs]


@app.post("/api/orders", status_code=201)
def create_order(order: Order):
    try:
        oid = create_document("order", order)
        return {"id": oid, "status": order.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class StatusUpdate(BaseModel):
    status: Order.model_fields["status"].annotation  # reuse literal type


@app.patch("/api/orders/{order_id}/status")
def update_order_status(order_id: str, payload: StatusUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order id")
    res = db["order"].update_one({"_id": ObjectId(order_id)}, {"$set": {"status": payload.status}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    doc = db["order"].find_one({"_id": ObjectId(order_id)})
    return serialize_doc(doc)


# Schemas endpoint for admin tooling
@app.get("/schema")
def get_schemas():
    return {
        "models": ["User", "Driver", "Order", "Payment"],
        "collections": ["user", "driver", "order", "payment"],
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
