from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text

from database import Base
from merger_events import MergerEvent, parse_merger_events


class Municipality(Base):
    __tablename__ = "municipalities"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(5), unique=True, index=True, nullable=False)
    parent_code = Column(String(5), index=True, nullable=True)
    prefecture_code = Column(String(2), index=True, nullable=False)
    prefecture_name = Column(String, index=True, nullable=False)
    district_name = Column(String, index=True, nullable=True)
    district_kana = Column(String, nullable=True)
    municipality_name = Column(String, index=True, nullable=True)
    municipality_kana = Column(String, nullable=True)
    effective_date = Column(Date, index=True, nullable=True)
    has_merger_info = Column(Boolean, nullable=False, default=False)


class Merger(Base):
    __tablename__ = "mergers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(5), index=True, nullable=False)
    prefecture_code = Column(String(2), index=True, nullable=False)
    prefecture_name = Column(String, index=True, nullable=False)
    district_name = Column(String, index=True, nullable=True)
    district_kana = Column(String, nullable=True)
    municipality_name = Column(String, index=True, nullable=True)
    municipality_kana = Column(String, nullable=True)
    effective_date = Column(Date, index=True, nullable=True)
    reason = Column(Text, nullable=False)

    @property
    def reason_events(self) -> list[MergerEvent]:
        return parse_merger_events(
            self.reason,
            fallback_target_code=self.code,
            fallback_target_names=[
                name
                for name in [self.municipality_name, self.district_name]
                if name is not None
            ],
        )


class SourceFileState(Base):
    __tablename__ = "source_file_states"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, unique=True, index=True, nullable=False)
    path = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    mtime = Column(DateTime(timezone=True), nullable=False)
    sha256 = Column(String(64), nullable=False)
    imported_at = Column(DateTime(timezone=True), nullable=False)
    row_count = Column(Integer, nullable=False)
