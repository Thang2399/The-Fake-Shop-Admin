from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List
from pydantic.config import ConfigDict

class CreateItem(BaseModel):
    name: str = Field(..., min_length=1)
    currency: str = Field("$")
    price: int = Field(0, ge=0)
    description: str | None = None
    imageUrl: str | None = None
    brandId: str = Field(..., min_length=1)
    categoryId: str = Field(..., min_length=1)
    subCategoryId: str = Field(..., min_length=1)
    quantity: int = Field(0, ge=0)
    isFavoriteItem: bool = False


class UpdateItem(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    currency: str | None = None
    price: int | None= Field(default=None, ge=0)
    description: str | None = None
    imageUrl: str | None = None
    brandId: str | None = None
    categoryId: str | None = None
    subCategoryId: str | None = None
    quantity: int | None = Field(default=None, ge=0)
    isFavoriteItem: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("name", "currency", "price", "description", "imageUrl", "brandId", "categoryId", "subCategoryId", "quantity", "isFavoriteItem", mode="before")

    @classmethod
    def _strip_strings(cls, v):
        if isinstance(v, str):
            v = v.strip()
        return v


class ItemResponse(BaseModel):
    id: str = Field(alias="_id")  # ← maps Mongo `_id` to model field `id`
    name: str
    currency: str
    price: int
    description: str | None = None
    imageUrl: str | None = None
    brandId: str
    categoryId: str
    subCategoryId: str
    quantity: int
    isFavoriteItem: bool


class DeleteItems(BaseModel):
    ids: List[str] = Field(..., description="Array of item ids")

    @field_validator('ids')
    @classmethod
    def validate_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValidationError("ids cannot be empty")
        bad = [s for s in v if not ObjectId.is_valid(s)]
        if bad:
            raise ValidationError(f'Invalid id(s): {', '.join(bad)}')
        return v

class BulkDeleteItemResponse(BaseModel):
    requested: int
    deleted: int
    not_found: list[str] = []
