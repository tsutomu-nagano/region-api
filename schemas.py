from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class MunicipalityBase(BaseModel):
    code: str
    prefecture_code: str
    name: str
    kana: Optional[str] = None

class Municipality(MunicipalityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class MergerBase(BaseModel):
    effective_date: date
    reason: str
    old_code: str
    old_name: str
    new_code: str
    new_name: str

class Merger(MergerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
