from database import SessionLocal, engine
import models
from datetime import date

def seed_data():
    # テーブルが存在しない場合は作成
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # すでにデータが存在するか確認
    if db.query(models.Municipality).first():
        print("Data already seeded.")
        return

    # 市区町村のサンプルデータ
    municipalities = [
        models.Municipality(code="13101", prefecture_code="13", name="千代田区", kana="ちよだく"),
        models.Municipality(code="13102", prefecture_code="13", name="中央区", kana="ちゅうおうく"),
        models.Municipality(code="11100", prefecture_code="11", name="さいたま市", kana="さいたまし"),
        models.Municipality(code="11201", prefecture_code="11", name="川越市", kana="かわごえし")
    ]
    db.add_all(municipalities)

    # 廃置分合（合併など）のサンプルデータ
    # 例：2001年5月1日 浦和市、大宮市、与野市が新設合併しさいたま市に
    mergers = [
        models.Merger(
            effective_date=date(2001, 5, 1),
            reason="新設合併",
            old_code="11204", old_name="浦和市",
            new_code="11100", new_name="さいたま市"
        ),
        models.Merger(
            effective_date=date(2001, 5, 1),
            reason="新設合併",
            old_code="11205", old_name="大宮市",
            new_code="11100", new_name="さいたま市"
        ),
        models.Merger(
            effective_date=date(2001, 5, 1),
            reason="新設合併",
            old_code="11215", old_name="与野市",
            new_code="11100", new_name="さいたま市"
        )
    ]
    db.add_all(mergers)

    # コミットして保存
    db.commit()
    print("Seed data inserted successfully.")

if __name__ == "__main__":
    seed_data()
