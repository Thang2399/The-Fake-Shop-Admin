from typing import List

from pydantic import BaseModel, ConfigDict, field_validator, Field


class SubCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subCategoryId: str = Field(..., min_length=1)

    @field_validator("subCategoryId", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

class Brand(BaseModel):
    brandId: str = Field(..., min_length=1)

    @field_validator("brandId", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

class CreateCategory(BaseModel):
    categoryName: str = Field(..., min_length=1)
    rootCategoryId: str | None = None
    subCategories: List[SubCategory] = Field(default_factory=list)
    brands: list[Brand] = Field(default_factory=list)

    @field_validator("categoryName", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

class CategoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    categoryName: str
    rootCategoryId: str | None = None
    subCategories: list[SubCategory]
    brands: list[Brand]

class UpdateCategory(BaseModel):
    categoryName: str | None = Field(default=None, min_length=1)
    rootCategoryId: str | None = None
    subCategories: list[SubCategory] = Field(default_factory=list)
    brands: list[Brand] = Field(default_factory=list)
    @field_validator("categoryName", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v
