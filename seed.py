import argparse

from database import SessionLocal
from importer import refresh_from_csv


def seed_data(force: bool = False):
    db = SessionLocal()
    try:
        refreshed, states = refresh_from_csv(db, force=force)
        print(f"CSV import refreshed={refreshed}")
        for state in states:
            print(f"{state.source_name}: {state.row_count} rows from {state.path}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSVから標準地域・廃置分合DBを更新します。")
    parser.add_argument(
        "--force",
        action="store_true",
        help="CSVの内容に変更がない場合も再取り込みします。",
    )
    args = parser.parse_args()
    seed_data(force=args.force)
