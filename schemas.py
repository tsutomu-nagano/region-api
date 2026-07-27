from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from merger_events import MergerEvent


class Municipality(BaseModel):
    id: int = Field(description="内部ID。")
    code: str = Field(description="5桁の標準地域コード。", examples=["01101"])
    parent_code: Optional[str] = Field(
        default=None,
        description="親となる標準地域コード。政令市の行政区などで設定されます。",
        examples=["01100"],
    )
    prefecture_code: str = Field(description="2桁の都道府県コード。", examples=["01"])
    prefecture_name: str = Field(description="都道府県名。", examples=["北海道"])
    district_name: Optional[str] = Field(
        default=None,
        description="政令市・郡・支庁・振興局等の名称。",
        examples=["札幌市"],
    )
    district_kana: Optional[str] = Field(default=None, description="district_name のふりがな。")
    municipality_name: Optional[str] = Field(
        default=None,
        description="市区町村名。政令市本体など、市区町村欄が空の行では null。",
        examples=["中央区"],
    )
    municipality_kana: Optional[str] = Field(default=None, description="municipality_name のふりがな。")
    effective_date: Optional[date] = Field(
        default=None,
        description="廃置分合等の施行年月日。",
        examples=["1972-04-01"],
    )
    has_merger_info: bool = Field(description="廃置分合等情報の有無。")

    model_config = ConfigDict(from_attributes=True)


class Merger(BaseModel):
    id: int = Field(description="内部ID。")
    code: str = Field(
        description="この廃置分合情報行の5桁の標準地域コード。",
        examples=["01236"],
    )
    prefecture_code: str = Field(description="2桁の都道府県コード。", examples=["01"])
    prefecture_name: str = Field(description="都道府県名。", examples=["北海道"])
    district_name: Optional[str] = Field(
        default=None,
        description="政令市・郡・支庁・振興局等の名称。",
        examples=["渡島支庁"],
    )
    district_kana: Optional[str] = Field(default=None, description="district_name のふりがな。")
    municipality_name: Optional[str] = Field(
        default=None,
        description="市区町村名。政令市本体など、市区町村欄が空の行では null。",
        examples=["北斗市"],
    )
    municipality_kana: Optional[str] = Field(default=None, description="municipality_name のふりがな。")
    effective_date: Optional[date] = Field(
        default=None,
        description="廃置分合等の施行年月日。",
        examples=["2006-02-01"],
    )
    reason: str = Field(
        description="CSV の改正事由をそのまま保持した人間向け説明文。",
        examples=["上磯町(01335)、大野町(01336)が合併し、北斗市(01236)を新設"],
    )
    reason_events: list[MergerEvent] = Field(
        default_factory=list,
        description="改正事由を機械判読しやすいイベント配列へ解析したもの。reason は原文、reason_events は補助的な構造化表現です。",
    )

    model_config = ConfigDict(from_attributes=True)


class SourceFileState(BaseModel):
    source_name: str = Field(description="取り込み元の識別名。", examples=["merger"])
    path: str = Field(description="取り込み元CSVのパス。")
    size: int = Field(description="CSVファイルサイズ。")
    mtime: datetime = Field(description="CSVファイルの最終更新日時。")
    sha256: str = Field(description="CSVファイル内容の SHA-256。")
    imported_at: datetime = Field(description="DBへ取り込んだ日時。")
    row_count: int = Field(description="取り込み行数。")

    model_config = ConfigDict(from_attributes=True)
