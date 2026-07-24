import csv
import hashlib
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import models


BASE_DIR = Path(__file__).resolve().parent
MUNICIPALITY_CSV = BASE_DIR / "Municipality.csv"
MERGER_CSV = BASE_DIR / "Merger.csv"


def parse_date(value: str) -> Optional[date]:
    value = (value or "").strip()
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def none_if_blank(value: str) -> Optional[str]:
    value = (value or "").strip()
    return value or None


def file_fingerprint(path: Path) -> dict:
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(path),
        "size": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        "sha256": digest.hexdigest(),
    }


def has_source_changed(db: Session, source_name: str, path: Path) -> bool:
    current = file_fingerprint(path)
    previous = (
        db.query(models.SourceFileState)
        .filter(models.SourceFileState.source_name == source_name)
        .one_or_none()
    )
    return previous is None or previous.sha256 != current["sha256"]


def read_csv_rows(path: Path) -> Iterable[dict]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        yield from csv.DictReader(file)


def municipality_parent_key(row: dict) -> tuple[str, str]:
    return (
        row["都道府県"].strip(),
        row["政令市･郡･支庁･振興局等"].strip(),
    )


def build_parent_code_lookup(rows: list[dict]) -> dict[tuple[str, str], str]:
    parents = {}
    for row in rows:
        key = municipality_parent_key(row)
        if key[1] and not row["市区町村"].strip():
            parents[key] = row["標準地域コード"].strip()
    return parents


def build_municipality(row: dict, parent_codes: dict[tuple[str, str], str]) -> models.Municipality:
    code = row["標準地域コード"].strip()
    parent_code = None
    if row["市区町村"].strip():
        parent_code = parent_codes.get(municipality_parent_key(row))
    return models.Municipality(
        code=code,
        parent_code=parent_code,
        prefecture_code=code[:2],
        prefecture_name=row["都道府県"].strip(),
        district_name=none_if_blank(row["政令市･郡･支庁･振興局等"]),
        district_kana=none_if_blank(row["政令市･郡･支庁･振興局等（ふりがな）"]),
        municipality_name=none_if_blank(row["市区町村"]),
        municipality_kana=none_if_blank(row["市区町村（ふりがな）"]),
        effective_date=parse_date(row["廃置分合等施行年月日"]),
        has_merger_info=row["廃置分合等情報有無"].strip() == "有",
    )


def build_merger(row: dict) -> models.Merger:
    code = row["標準地域コード"].strip()
    return models.Merger(
        code=code,
        prefecture_code=code[:2],
        prefecture_name=row["都道府県"].strip(),
        district_name=none_if_blank(row["政令市･郡･支庁･振興局等"]),
        district_kana=none_if_blank(row["政令市･郡･支庁･振興局等（ふりがな）"]),
        municipality_name=none_if_blank(row["市区町村"]),
        municipality_kana=none_if_blank(row["市区町村（ふりがな）"]),
        effective_date=parse_date(row["廃置分合等施行年月日"]),
        reason=row["改正事由"].strip(),
    )


def replace_source(
    db: Session,
    source_name: str,
    path: Path,
    model: type,
    rows: list,
) -> models.SourceFileState:
    db.query(model).delete()
    db.add_all(rows)

    current = file_fingerprint(path)
    state = (
        db.query(models.SourceFileState)
        .filter(models.SourceFileState.source_name == source_name)
        .one_or_none()
    )
    if state is None:
        state = models.SourceFileState(source_name=source_name)
        db.add(state)

    state.path = current["path"]
    state.size = current["size"]
    state.mtime = current["mtime"]
    state.sha256 = current["sha256"]
    state.imported_at = datetime.now(timezone.utc)
    state.row_count = len(rows)
    return state


def refresh_from_csv(db: Session, force: bool = False) -> tuple[bool, list[models.SourceFileState]]:
    schema_changed = ensure_current_schema(db)
    lock_refresh(db)

    changed = force or schema_changed
    changed = changed or has_source_changed(db, "municipality", MUNICIPALITY_CSV)
    changed = changed or has_source_changed(db, "merger", MERGER_CSV)

    if changed:
        municipality_rows = list(read_csv_rows(MUNICIPALITY_CSV))
        parent_codes = build_parent_code_lookup(municipality_rows)
        municipalities = [build_municipality(row, parent_codes) for row in municipality_rows]
        mergers = [build_merger(row) for row in read_csv_rows(MERGER_CSV)]
        replace_source(db, "municipality", MUNICIPALITY_CSV, models.Municipality, municipalities)
        replace_source(db, "merger", MERGER_CSV, models.Merger, mergers)
        db.commit()

    states = db.query(models.SourceFileState).order_by(models.SourceFileState.source_name).all()
    return changed, states


def lock_refresh(db: Session) -> None:
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(7420250724)"))


def ensure_current_schema(db: Session) -> bool:
    bind = db.get_bind()
    inspector = inspect(bind)
    schema_changed = False
    required_columns = {
        "municipalities": {
            "code",
            "parent_code",
            "prefecture_code",
            "prefecture_name",
            "district_name",
            "district_kana",
            "municipality_name",
            "municipality_kana",
            "effective_date",
            "has_merger_info",
        },
        "mergers": {
            "code",
            "prefecture_code",
            "prefecture_name",
            "district_name",
            "district_kana",
            "municipality_name",
            "municipality_kana",
            "effective_date",
            "reason",
        },
        "source_file_states": {
            "source_name",
            "path",
            "size",
            "mtime",
            "sha256",
            "imported_at",
            "row_count",
        },
    }

    stale_tables = []
    for table_name, columns in required_columns.items():
        if not inspector.has_table(table_name):
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        if table_name == "municipalities" and "parent_code" not in existing_columns:
            db.execute(text("ALTER TABLE municipalities ADD COLUMN parent_code VARCHAR(5)"))
            existing_columns.add("parent_code")
            schema_changed = True
        if not columns.issubset(existing_columns):
            stale_tables.append(table_name)
        if table_name == "mergers":
            unique_names = {
                constraint.get("name")
                for constraint in inspector.get_unique_constraints(table_name)
            }
            if "uq_mergers_code_date_reason" in unique_names:
                stale_tables.append(table_name)

    allow_destructive_schema_sync = (
        os.getenv("ALLOW_DESTRUCTIVE_SCHEMA_SYNC", "false").lower() == "true"
        or bind.dialect.name == "sqlite"
    )

    if stale_tables and allow_destructive_schema_sync:
        for table in reversed(models.Base.metadata.sorted_tables):
            if table.name in stale_tables:
                table.drop(bind=bind, checkfirst=True)
    elif stale_tables:
        raise RuntimeError(
            "DB schema is stale for tables: "
            + ", ".join(sorted(set(stale_tables)))
            + ". Run a migration or set ALLOW_DESTRUCTIVE_SCHEMA_SYNC=true for disposable databases."
        )

    models.Base.metadata.create_all(bind=bind)
    return schema_changed
