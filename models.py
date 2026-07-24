from sqlalchemy import Column, Integer, String, Date
from database import Base

class Municipality(Base):
    __tablename__ = "municipalities"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True) # 市区町村コード
    prefecture_code = Column(String, index=True)   # 都道府県コード
    name = Column(String, index=True)              # 市区町村名
    kana = Column(String)                          # ふりがな

class Merger(Base):
    __tablename__ = "mergers"

    id = Column(Integer, primary_key=True, index=True)
    effective_date = Column(Date, index=True)      # 施行日
    reason = Column(String)                        # 事由 (新設合併, 編入合併, 境界変更など)
    old_code = Column(String, index=True)          # 旧市区町村コード
    old_name = Column(String)                      # 旧市区町村名
    new_code = Column(String, index=True)          # 新市区町村コード
    new_name = Column(String)                      # 新市区町村名
