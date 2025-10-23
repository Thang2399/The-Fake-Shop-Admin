from fastapi import APIRouter
from app.db import db
from bson import ObjectId

router = APIRouter(prefix="/admin/items", tags=["Items"])

def serialize_document(doc):
    """Convert ObjectId to string for JSON serialization."""
    doc["_id"] = str(doc["_id"])
    return doc

@router.get('/')
async def get_list_items():
    raw_items = await db.items.find().to_list(length=1000)  # You can set the max number here
    print('items', raw_items)
    # return {"status": "connected"}
    return [serialize_document(item) for item in raw_items]
