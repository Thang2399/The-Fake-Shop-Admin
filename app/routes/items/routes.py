from fastapi import APIRouter, HTTPException, status
from pymongo import ReturnDocument

from app.common.mongo_utils import serialize_document, to_object_id
from app.db import db
from bson import ObjectId

from app.models.item import ItemResponse, CreateItem, BulkDeleteItemResponse, DeleteItems, UpdateItem

router = APIRouter(prefix="/admin/items", tags=["Items"])


@router.get('/')
async def get_list_items():
    raw_items = await db.items.find().to_list(length=1000)  # You can set the max number here
    print('items', raw_items)
    return [serialize_document(item) for item in raw_items]


@router.get("/{id}")
async def get_detail_item(id: str):
    to_object_id(id)

    doc = await db.items.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item not found: {id}')
    return serialize_document(doc)


@router.post('/', response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(payload: CreateItem):
    try:
        # Turn Pydantic model into a plain dict for MongoDB
        doc = payload.model_dump(exclude_none=True)  # Pydantic v2; use .dict() in v1

        # Optional: normalize/trim incoming string IDs
        doc["categoryId"] = doc["categoryId"].strip()
        doc["subCategoryId"] = doc["subCategoryId"].strip()
        result = await db.items.insert_one(doc)
        created = await db.items.find_one({"_id": result.inserted_id})
        return serialize_document(created)  # converts _id -> id for JSON

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete('/', response_model=BulkDeleteItemResponse, status_code=status.HTTP_200_OK)
async def delete_items(payload: DeleteItems):
    obj_ids = [to_object_id(x) for x in payload.ids]

    existing = await db.items.find(
        {"_id": {"$in": obj_ids}},
        {"_id": 1}
    ).to_list(length=len(obj_ids))
    existing_ids = {str(doc["_id"]) for doc in existing}
    not_found = [x for x in payload.ids if x not in existing_ids]

    result = await db.items.delete_many({"_id": {"$in": obj_ids}})
    return BulkDeleteItemResponse(
        requested=len(payload.ids),
        deleted=result.deleted_count or 0,
        not_found=not_found,
    )

@router.patch("/{id}", response_model=ItemResponse, status_code=status.HTTP_202_ACCEPTED)
async def update_item(id: str, payload: UpdateItem):
    to_object_id(id)

    update_doc = payload.model_dump(exclude_unset= True, exclude_none=True)
    update_doc.pop("_id", None)
    update_doc.pop("id", None)

    if not update_doc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Invalid fields to update')

    updated = await db.items.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": update_doc},
        return_document=ReturnDocument.AFTER
    )

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item not found: {id}')
    return serialize_document(updated)
