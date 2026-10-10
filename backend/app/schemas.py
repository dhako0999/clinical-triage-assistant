from pydantic import BaseModel, Field
from typing import Literal


class SiteQueryCreate(BaseModel):
    site_id: str = Field(min_length=1, max_length=50)
    query_text: str = Field(min_length=1, max_length=5000)


class ReviewActionCreate(BaseModel):
    reviewer_name: str = Field(min_length=1, max_length=100)
    action: Literal["approve", "edit", "reject"]
    edited_response: str | None = Field(default=None, max_length=5000)