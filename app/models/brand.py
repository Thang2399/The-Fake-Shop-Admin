from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationError
from typing import List


class CategoryId(BaseModel):
    model_config = ConfigDict(extra="forbid")
    categoryId: str = Field(..., min_length=1)

    @field_validator("categoryId", mode='before')
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

class CreateBrand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    brandName: str = Field(..., min_length=1)
    brandSymbol: str = Field(..., min_length=1)
    brandIcon : str | None = None
    categoryIdList: list[CategoryId] = Field(default_factory=list)

    @field_validator("brandName", "brandSymbol", "brandIcon", mode='before')
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v

class BrandResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    brandName: str
    brandSymbol: str
    brandIcon: str | None = None
    categoryIdList: list[CategoryId]

class DeleteBrands(BaseModel):
    ids: List[str] = Field(..., description="Array of brand ids")

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValidationError("ids cannot be empty")
        bad = [s for s in v if not ObjectId.is_valid(s)]
        if bad:
            raise ValidationError(f"Invalid id(s): {', '.join(bad)}")
        return v

class BulkDeleteBrandResponse(BaseModel):
    requested: int
    deleted: int
    not_found: list[str] = []

class UpdateBrand(BaseModel):
    brandName: str | None = Field(default=None, min_length=1)
    brandSymbol: str | None = None
    brandIcon: str | None = None
    categoryIdList: list[CategoryId] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
    @field_validator("brandName", "brandSymbol", "brandIcon", mode='before')
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v
