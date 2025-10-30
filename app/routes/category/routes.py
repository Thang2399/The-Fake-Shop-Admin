import datetime
from typing import Set, Dict, Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.common.mongo_utils import serialize_document, to_object_id, extract_ids
from app.db import db
from app.models.category import CategoryResponse, CreateCategory, Brand, UpdateCategory

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

async def update_brands(brands: list[Brand], created_category_id: ObjectId):
    brand_ids_str = extract_ids(brands, "brandId")
    brand_ids = [to_object_id(x) for x in brand_ids_str]

    # Update brand
    if brand_ids:
        updated_brands = await db.brands.update_many(
            {"_id": {"$in": brand_ids}},
            {"$addToSet": {"categoryIdList": {"categoryId": str(created_category_id)}}}
        )
        if updated_brands.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

async def update_root_category(root_category_id: str, created_category_id: ObjectId):
    root_category_oid = to_object_id(root_category_id)
    updated_root_category = await db.categories.update_one(
        {"_id": root_category_oid},
        {"$addToSet": {"subCategories": {"subCategoryId": str(created_category_id)}}}
    )
    if updated_root_category.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Root Category not found")

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CreateCategory):
    try:
        doc = payload.model_dump(exclude_none=True)
        result = await db.categories.insert_one(doc)
        created_category_id = result.inserted_id
        created_category = await db.categories.find_one({"_id": created_category_id})

        # Update brand
        if payload.brands:
            await update_brands(payload.brands, created_category_id)

        # Update rootId
        if payload.rootCategoryId:
            await update_root_category(payload.rootCategoryId, created_category_id)

        return serialize_document(created_category)

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

def normalize_brand_oid_set(raw: Any) -> Set[ObjectId]:
    """
    Accept either:
      - [ObjectId, ...]
      - [{"brandId": <OID|str>}, ...]
    Return a set of ObjectIds.
    """
    if not raw:
        return set()
    s: Set[ObjectId] = set()
    for it in raw:
        if isinstance(it, ObjectId):
            s.add(it)
        elif isinstance(it, dict) and "brandId" in it:
            s.add(to_object_id(it["brandId"]))
        else:
            # tolerate stray strings
            s.add(to_object_id(it))
    return s

def normalize_sub_oid_set(raw: Any) -> Set[ObjectId]:
    """
    Accept list like:
      - [{"subCategoryId": <OID|str>}, ...]
      - [<OID|str>, ...]  (if you happened to store raw IDs)
    Return a set of ObjectIds.
    """
    if not raw:
        return set()
    s: Set[ObjectId] = set()
    for it in raw:
        if isinstance(it, dict) and "subCategoryId" in it:
            s.add(to_object_id(it["subCategoryId"]))
        else:
            s.add(to_object_id(it))
    return s

@router.patch("/{id}", response_model=CategoryResponse, status_code=status.HTTP_202_ACCEPTED)
async def update_category(id: str, payload: UpdateCategory):
    cat_id = to_object_id(id)

    current = await db.categories.find_one({"_id": cat_id})
    if not current:
        raise HTTPException(status_code=404, detail="Category not found")

    # --- NEW values from payload ------------------------------------------
    # Brands
    new_brand_id_strs = extract_ids(payload.brands, "brandId")
    new_brand_oids = [to_object_id(x) for x in new_brand_id_strs]
    new_brand_oid_set: Set[ObjectId] = set(new_brand_oids)

    # SubCategories
    new_sub_id_strs = extract_ids(payload.subCategories, "subCategoryId")
    new_sub_oids = [to_object_id(x) for x in new_sub_id_strs]
    new_sub_oid_set: Set[ObjectId] = set(new_sub_oids)

    # Root
    new_root_oid = None
    if payload.rootCategoryId is not None:
        new_root_oid = to_object_id(payload.rootCategoryId) if payload.rootCategoryId else None

    # --- EXISTING values from DB ------------------------------------------
    # Brands may be stored as [ObjectId] or [{"brandId": <id>}]
    existing_brand_oid_set: Set[ObjectId] = normalize_brand_oid_set(current.get("brands", []))

    # SubCategories usually stored as [{"subCategoryId": <id>}]
    existing_sub_oid_set: Set[ObjectId] = normalize_sub_oid_set(current.get("subCategories", []))

    existing_root_oid = None
    if current.get("rootCategoryId") is not None:
        try:
            existing_root_oid = to_object_id(current["rootCategoryId"])
        except HTTPException:
            existing_root_oid = None  # tolerate legacy bad value

    # --- compute diffs -----------------------------------------------------
    to_add_brands = new_brand_oid_set - existing_brand_oid_set
    to_remove_brands = existing_brand_oid_set - new_brand_oid_set

    to_add_subs = new_sub_oid_set - existing_sub_oid_set
    to_remove_subs = existing_sub_oid_set - new_sub_oid_set

    root_changed = (existing_root_oid != new_root_oid)

    # --- write category doc ------------------------------------------------
    category_set: Dict[str, Any] = {}

    if payload.categoryName is not None:
        category_set["categoryName"] = payload.categoryName

    # Store root as ObjectId (recommended)
    if payload.rootCategoryId is not None:
        category_set["rootCategoryId"] = new_root_oid

    # Replace full lists with normalized forms
    # Store brands as list[ObjectId]
    category_set["brands"] = list(new_brand_oid_set)

    # Store subCategories as objects with ObjectId inside (works with your serializers)
    category_set["subCategories"] = [{"subCategoryId": oid} for oid in new_sub_oid_set]

    await db.categories.update_one({"_id": cat_id}, {"$set": category_set})

    # --- sync inverse relations -------------------------------------------
    # Brands: keep string categoryId in brand.categoryIdList for portability
    if to_add_brands:
        await db.brands.update_many(
            {"_id": {"$in": list(to_add_brands)}},
            {"$addToSet": {"categoryIdList": {"categoryId": str(cat_id)}}},
        )
    if to_remove_brands:
        await db.brands.update_many(
            {"_id": {"$in": list(to_remove_brands)}},
            {"$pull": {"categoryIdList": {"categoryId": str(cat_id)}}},
        )

    # SubCategories: mirror the same pattern (categoryIdList on subcategories)
    if to_add_subs:
        await db.categories.update_many(
            {"_id": {"$in": list(to_add_subs)}},
            {"$addToSet": {"categoryIdList": {"categoryId": str(cat_id)}}},
        )
    if to_remove_subs:
        await db.categories.update_many(
            {"_id": {"$in": list(to_remove_subs)}},
            {"$pull": {"categoryIdList": {"categoryId": str(cat_id)}}},
        )

    # Root category parent: move this category between parents' children
    if root_changed:
        # Remove from old parent
        if existing_root_oid:
            await db.categories.update_one(
                {"_id": existing_root_oid},
                {"$pull": {"subCategories": {"categoryId": str(cat_id)}}},
            )
        # Add to new parent
        if new_root_oid:
            await db.categories.update_one(
                {"_id": new_root_oid},
                {"$addToSet": {"subCategories": {"categoryId": str(cat_id)}}},
            )

    # --- return fresh document --------------------------------------------
    updated = await db.categories.find_one({"_id": cat_id})
    # Important: return via response model so serializers run
    return serialize_document(updated)
