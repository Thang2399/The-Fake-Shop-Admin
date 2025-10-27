from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pymongo import ReturnDocument

from app.common.mongo_utils import serialize_document, to_object_id, find_existing_and_missing_ids
from app.db import db
from app.models.brand import BrandResponse, CreateBrand, BulkDeleteBrandResponse, DeleteBrands, UpdateBrand

router = APIRouter(prefix='/admin/brands', tags=['Brands'])

@router.get('/')
async def get_list_brand():
    raw_brands = await db.brands.find().to_list(length=100)
    return [serialize_document(br) for br in raw_brands]

@router.get("/{id}")
async def get_detail_brand(id: str):
    to_object_id(id)

    doc = await db.brands.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return serialize_document(doc)

@router.post('/', response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(payload: CreateBrand):
    try:
        doc = payload.model_dump(exclude_none=True)
        result = await db.brands.insert_one(doc)
        created_brand = await db.brands.find_one({"_id": result.inserted_id})
        return serialize_document(created_brand)
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

@router.delete('/', response_model=BulkDeleteBrandResponse, status_code=status.HTTP_200_OK)
async def delete_brand(payload: DeleteBrands):
    ids = payload.ids
    existing_ids, not_found = await find_existing_and_missing_ids(db.brands, ids)
    obj_ids = [to_object_id(x) for x in existing_ids]
    result = await db.brands.delete_many({"_id": {"$in": obj_ids}})
    return BulkDeleteBrandResponse(
        requested=len(ids),
        deleted=result.deleted_count or 0,
        not_found=not_found
    )

@router.patch('/{id}', response_model=BrandResponse, status_code=status.HTTP_202_ACCEPTED)
async def update_brand(id: str, payload: UpdateBrand):
    object_id = to_object_id(id)
    update_doc = payload.model_dump(exclude_unset=True, exclude_none=True)
    update_doc.pop("_id", None)
    update_doc.pop("id", None)

    if not update_doc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid fields to update")

    updated = await db.brands.find_one_and_update(
        {"_id": object_id},
        {"$set": update_doc},
        return_document=ReturnDocument.AFTER
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return serialize_document(updated)