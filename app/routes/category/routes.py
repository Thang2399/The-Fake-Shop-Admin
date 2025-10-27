from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.common.mongo_utils import serialize_document, to_object_id
from app.db import db

router = APIRouter(prefix="/admin/categories", tags=["Category"])

@router.get("/")
async def get_list_categories():
    raw_categories = await db.categories.find().to_list(length=100)
    return [serialize_document(category) for category in raw_categories]

@router.get("/{id}")
async def get_detail_category(id: str):
    to_object_id(id)

    doc = await db.categories.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category not found: {id}")
    return serialize_document(doc)
