from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Municipality(BaseModel):
    id: int
    code: str
    prefecture_code: str
    prefecture_name: str
    district_name: Optional[str] = None
    district_kana: Optional[str] = None
    municipality_name: Optional[str] = None
    municipality_kana: Optional[str] = None
    effective_date: Optional[date] = None
    has_merger_info: bool

    model_config = ConfigDict(from_attributes=True)


class Merger(BaseModel):
    id: int
    code: str
    prefecture_code: str
    prefecture_name: str
    district_name: Optional[str] = None
    district_kana: Optional[str] = None
    municipality_name: Optional[str] = None
    municipality_kana: Optional[str] = None
    effective_date: Optional[date] = None
    reason: str

    model_config = ConfigDict(from_attributes=True)


class SourceFileState(BaseModel):
    source_name: str
    path: str
    size: int
    mtime: datetime
    sha256: str
    imported_at: datetime
    row_count: int

    model_config = ConfigDict(from_attributes=True)
