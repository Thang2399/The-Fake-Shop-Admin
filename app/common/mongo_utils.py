from typing import Any, Dict, Iterable, Tuple, Set,List
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection


def to_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Invalid ObjectId: {id_str}')
    return ObjectId(id_str)

def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert objectId to string for JSON serialization."""
    _id = doc.get("_id")
    out = {k: v for k, v in doc.items() if k != "_id"}
    if isinstance(_id, ObjectId):
        out["_id"] = str(_id)
    elif _id is not None:
        out["_id"] = str(_id)
    return out

async def find_existing_and_missing_ids(
    collection: AsyncIOMotorCollection,
    ids: Iterable[str],
    *,
    id_field: str = "_id",
    ids_are_objectIds: bool = True,
) -> Tuple[Set[str], List[str]]:
    """
    Given a list of string ids, return (existing_ids, not_found).
    - existing_ids: set of stringified ids present in the collection
    - not_found: list of ids that were not found
    """
    ids_list = list(ids)
    if ids_are_objectIds:
        valid = [to_object_id(i) for i in ids_list]
        existing = await collection.find({id_field: {"$in": valid}}, {id_field: 1}).to_list(length=len(valid))
        existing_ids = {str(doc["_id"]) for doc in existing}
        not_found = {i for i in ids_list if i not in existing_ids}
    else:
        existing = await collection.find({id_field: {"$in": ids_list}}, {id_field: 1}).to_list(length=len(ids_list))
        existing_ids = {str(doc[id_field]) for doc in existing}
        not_found = [i for i in ids_list if i not in existing_ids]
    return existing_ids, not_found