from typing import Any, Dict, Iterable, Tuple, Set,List
from datetime import date, datetime
from bson import ObjectId, Decimal128
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection
import base64


def to_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Invalid ObjectId: {id_str}')
    return ObjectId(id_str)

def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively convert Mongo/BSON types to JSON-safe values."""
    def conv(v: Any):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, (datetime, date)):
            return v.isoformat()
        if isinstance(v, Decimal128):
            return float(v.to_decimal())
        if isinstance(v, bytes):
            return base64.b64encode(v).decode("utf-8")
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        if isinstance(v, (list, tuple, set)):
            return [conv(x) for x in v]
        return v

    return conv(doc)

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

def extract_ids(items: List[Dict[str, Any]] | None, key: str) -> List[str]:
    """From a list of dicts, pick string IDs under `key` (accepts str or ObjectId)."""
    out: List[str] = []
    if not items:
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        v = it.get(key)
        if isinstance(v, ObjectId):
            out.append(str(v))
        elif isinstance(v, str):
            out.append(v.strip())
    return out