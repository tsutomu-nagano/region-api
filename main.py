from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

import models
import schemas
from database import SessionLocal, engine

# DBテーブルの作成 (初回起動時用)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="市区町村情報 API",
    description="市区町村の一覧および廃置分合情報を取得するAPIです。",
    version="1.0.0"
)

# データベースセッションの依存性注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/municipalities", response_model=List[schemas.Municipality], summary="市区町村一覧の取得")
def read_municipalities(
    skip: int = Query(0, description="スキップする件数"),
    limit: int = Query(100, description="取得する最大件数"),
    prefecture_code: Optional[str] = Query(None, description="都道府県コードによる絞り込み"),
    db: Session = Depends(get_db)
):
    """
    市区町村の一覧を取得します。都道府県コードでのフィルタリングが可能です。
    """
    query = db.query(models.Municipality)
    if prefecture_code:
        query = query.filter(models.Municipality.prefecture_code == prefecture_code)
    return query.offset(skip).limit(limit).all()

@app.get("/api/v1/municipalities/mergers", response_model=List[schemas.Merger], summary="廃置分合情報の取得")
def read_mergers(
    skip: int = Query(0, description="スキップする件数"),
    limit: int = Query(100, description="取得する最大件数"),
    date_from: Optional[date] = Query(None, description="開始日 (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="終了日 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    市区町村の廃置分合（合併など）の履歴を取得します。
    期間（date_from, date_to）による絞り込みが可能です。
    """
    query = db.query(models.Merger)
    if date_from:
        query = query.filter(models.Merger.effective_date >= date_from)
    if date_to:
        query = query.filter(models.Merger.effective_date <= date_to)
    return query.offset(skip).limit(limit).all()
