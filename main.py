import os
from datetime import date
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

import models
import schemas
from database import SessionLocal, engine


models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="標準地域・廃置分合 API",
    description="Municipality.csv と Merger.csv をDBに同期し、標準地域および廃置分合情報を提供するAPIです。",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174",
    ).split(",")
    if origin.strip()
]
allowed_origin_regex = os.getenv(
    "CORS_ALLOW_ORIGIN_REGEX",
    r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/v1/municipalities", response_model=list[schemas.Municipality], summary="標準地域一覧の取得")
def read_municipalities(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大件数"),
    prefecture_code: Optional[str] = Query(None, description="都道府県コードによる絞り込み"),
    prefecture_name: Optional[str] = Query(None, description="都道府県名による絞り込み"),
    code: Optional[str] = Query(None, description="標準地域コードによる絞り込み"),
    parent_code: Optional[str] = Query(None, description="親の標準地域コードによる絞り込み"),
    has_merger_info: Optional[bool] = Query(None, description="廃置分合等情報有無による絞り込み"),
    effective_date_from: Optional[date] = Query(None, description="施行日の開始日 (YYYY-MM-DD)"),
    effective_date_to: Optional[date] = Query(None, description="施行日の終了日 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Municipality)
    if prefecture_code:
        query = query.filter(models.Municipality.prefecture_code == prefecture_code)
    if prefecture_name:
        query = query.filter(models.Municipality.prefecture_name == prefecture_name)
    if code:
        query = query.filter(models.Municipality.code == code)
    if parent_code:
        query = query.filter(models.Municipality.parent_code == parent_code)
    if has_merger_info is not None:
        query = query.filter(models.Municipality.has_merger_info == has_merger_info)
    if effective_date_from:
        query = query.filter(models.Municipality.effective_date >= effective_date_from)
    if effective_date_to:
        query = query.filter(models.Municipality.effective_date <= effective_date_to)
    return query.order_by(models.Municipality.code).offset(skip).limit(limit).all()


@app.get("/api/v1/mergers", response_model=list[schemas.Merger], summary="廃置分合情報の取得")
@app.get("/api/v1/municipalities/mergers", response_model=list[schemas.Merger], include_in_schema=False)
def read_mergers(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大件数"),
    prefecture_code: Optional[str] = Query(None, description="都道府県コードによる絞り込み"),
    prefecture_name: Optional[str] = Query(None, description="都道府県名による絞り込み"),
    code: Optional[str] = Query(None, description="標準地域コードによる絞り込み"),
    effective_date_from: Optional[date] = Query(None, description="施行日の開始日 (YYYY-MM-DD)"),
    effective_date_to: Optional[date] = Query(None, description="施行日の終了日 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Merger)
    if prefecture_code:
        query = query.filter(models.Merger.prefecture_code == prefecture_code)
    if prefecture_name:
        query = query.filter(models.Merger.prefecture_name == prefecture_name)
    if code:
        query = query.filter(models.Merger.code == code)
    if effective_date_from:
        query = query.filter(models.Merger.effective_date >= effective_date_from)
    if effective_date_to:
        query = query.filter(models.Merger.effective_date <= effective_date_to)
    return query.order_by(models.Merger.effective_date, models.Merger.code).offset(skip).limit(limit).all()


@app.get(
    "/api/v1/municipalities/search",
    response_model=list[schemas.Municipality],
    summary="市区町村名から標準地域を検索",
)
def search_municipalities_by_name(
    name: str = Query(..., min_length=1, description="検索する市区町村名またはふりがな"),
    match: Literal["exact", "partial"] = Query("exact", description="exact: 完全一致、partial: 部分一致"),
    prefecture_code: Optional[str] = Query(None, description="都道府県コードによる絞り込み"),
    prefecture_name: Optional[str] = Query(None, description="都道府県名による絞り込み"),
    include_district: bool = Query(
        True,
        description="partial検索時に政令市・郡・支庁・振興局等の名称/ふりがなも検索対象に含める",
    ),
    limit: int = Query(20, ge=1, le=100, description="取得する最大件数"),
    db: Session = Depends(get_db),
):
    normalized_name = name.strip()
    if not normalized_name:
        raise HTTPException(status_code=422, detail="name must not be blank")

    query = db.query(models.Municipality)
    if prefecture_code:
        query = query.filter(models.Municipality.prefecture_code == prefecture_code)
    if prefecture_name:
        query = query.filter(models.Municipality.prefecture_name == prefecture_name)

    if match == "exact":
        name_condition = or_(
            models.Municipality.municipality_name == normalized_name,
            models.Municipality.municipality_kana == normalized_name,
            and_(
                models.Municipality.municipality_name.is_(None),
                or_(
                    models.Municipality.district_name == normalized_name,
                    models.Municipality.district_kana == normalized_name,
                ),
            ),
        )
    else:
        pattern = f"%{normalized_name}%"
        conditions = [
            models.Municipality.municipality_name.ilike(pattern),
            models.Municipality.municipality_kana.ilike(pattern),
        ]
        if include_district:
            conditions.extend(
                [
                    models.Municipality.district_name.ilike(pattern),
                    models.Municipality.district_kana.ilike(pattern),
                ]
            )
        name_condition = or_(*conditions)

    return query.filter(name_condition).order_by(models.Municipality.code).limit(limit).all()


@app.get("/api/v1/municipalities/{code}", response_model=schemas.Municipality, summary="標準地域の取得")
def read_municipality(code: str, db: Session = Depends(get_db)):
    municipality = db.query(models.Municipality).filter(models.Municipality.code == code).one_or_none()
    if municipality is None:
        raise HTTPException(status_code=404, detail="Municipality not found")
    return municipality


@app.get(
    "/api/v1/municipalities/{code}/children",
    response_model=list[schemas.Municipality],
    summary="子の標準地域一覧の取得",
)
def read_municipality_children(code: str, db: Session = Depends(get_db)):
    return (
        db.query(models.Municipality)
        .filter(models.Municipality.parent_code == code)
        .order_by(models.Municipality.code)
        .all()
    )


@app.get("/api/v1/sources", response_model=list[schemas.SourceFileState], summary="CSV取り込み状態の取得")
def read_sources(db: Session = Depends(get_db)):
    return db.query(models.SourceFileState).order_by(models.SourceFileState.source_name).all()
