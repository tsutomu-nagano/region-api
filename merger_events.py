import re
from typing import Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "merge_new",
    "absorption",
    "new_establishment",
    "split",
    "city_status",
    "town_status",
    "rename",
    "designated_city",
    "core_city",
    "special_city",
]


class MunicipalityRef(BaseModel):
    code: str | None = Field(
        default=None,
        description="標準地域コード。改正事由の文中にコードがなく補完もできない場合は null。",
        examples=["01236"],
    )
    name: str = Field(description="自治体名または行政区名。", examples=["北斗市"])
    code_inferred: bool = Field(
        default=False,
        description="true の場合、code は改正事由の文中ではなくレスポンス行の標準地域コードから補完した値。",
    )


class MergerEvent(BaseModel):
    type: EventType = Field(
        description="機械判読用のイベント種別。例: merge_new は合併して新自治体を設置、absorption は編入。",
        examples=["merge_new"],
    )
    label: str = Field(description="イベント種別の日本語表示名。", examples=["合併・新設"])
    source_municipalities: list[MunicipalityRef] = Field(
        default_factory=list,
        description="変更元・消滅側・移行前として読み取れる自治体。",
    )
    target_municipalities: list[MunicipalityRef] = Field(
        default_factory=list,
        description="変更先・新設側・編入先・移行後として読み取れる自治体。",
    )


MUNICIPALITY_REF_RE = re.compile(r"([^、。\r\nしがにの（）()]+)[（(](\d{5})[）)]")
TARGET_REF_RE = re.compile(r"([^、。\r\nしがにの（）()]+?)(?:[（(](\d{5})[）)])?(?:を|に)")


EVENT_LABELS: dict[EventType, str] = {
    "merge_new": "合併・新設",
    "absorption": "編入",
    "new_establishment": "新設",
    "split": "分離",
    "city_status": "市制施行",
    "town_status": "町制施行",
    "rename": "名称変更",
    "designated_city": "政令指定都市施行",
    "core_city": "中核市移行",
    "special_city": "特例市移行",
}


def parse_municipality_refs(text: str) -> list[MunicipalityRef]:
    seen = set()
    refs = []
    for name, code in MUNICIPALITY_REF_RE.findall(text):
        ref = MunicipalityRef(code=code, name=name.strip())
        key = (ref.code, ref.name)
        if key not in seen:
            refs.append(ref)
            seen.add(key)
    return refs


def parse_target_refs(text: str) -> list[MunicipalityRef]:
    refs = []
    seen = set()
    for name, code in TARGET_REF_RE.findall(text):
        name = name.strip(" 、。\r\n")
        if not name or re.search(r"[がをにの]$", name):
            continue
        ref = MunicipalityRef(code=code or None, name=name)
        key = (ref.code, ref.name)
        if key not in seen:
            refs.append(ref)
            seen.add(key)
    return refs


def infer_target_codes(
    refs: list[MunicipalityRef],
    fallback_code: str | None = None,
    fallback_names: list[str] | None = None,
) -> list[MunicipalityRef]:
    if not fallback_code or not fallback_names:
        return refs

    fallback_name_set = {name for name in fallback_names if name}
    inferred_refs = []
    for ref in refs:
        if ref.code is None and ref.name in fallback_name_set:
            inferred_refs.append(
                MunicipalityRef(code=fallback_code, name=ref.name, code_inferred=True)
            )
        else:
            inferred_refs.append(ref)
    return inferred_refs


def event_types_for_reason(reason: str) -> list[EventType]:
    event_types: list[EventType] = []
    checks: list[tuple[EventType, bool]] = [
        ("merge_new", "合併" in reason and "新設" in reason),
        ("absorption", "編入" in reason),
        ("new_establishment", "新設" in reason),
        ("split", "分離" in reason),
        ("city_status", "市制施行" in reason),
        ("town_status", "町制施行" in reason),
        ("rename", "名称変更" in reason),
        ("designated_city", "政令指定都市施行" in reason),
        ("core_city", "中核市" in reason and "移行" in reason),
        ("special_city", "特例市" in reason and "移行" in reason),
    ]
    for event_type, matched in checks:
        if matched:
            event_types.append(event_type)
    return event_types


def parse_merger_events(
    reason: str,
    fallback_target_code: str | None = None,
    fallback_target_names: list[str] | None = None,
) -> list[MergerEvent]:
    events = []

    for event_type in event_types_for_reason(reason):
        event_text = reason
        source_text = reason
        if "が" in reason:
            source_text, event_text = reason.rsplit("が", 1)
        if event_type == "merge_new" and "合併し、" in reason:
            source_text = reason.split("が合併し、", 1)[0]
            event_text = reason.split("合併し、", 1)[1]
        elif event_type == "absorption" and "が" in reason:
            event_text = reason.rsplit("が", 1)[1]
        elif event_type == "new_establishment" and "し、" in reason:
            event_text = reason.rsplit("し、", 1)[1]

        events.append(
            MergerEvent(
                type=event_type,
                label=EVENT_LABELS[event_type],
                source_municipalities=parse_municipality_refs(source_text),
                target_municipalities=infer_target_codes(
                    parse_target_refs(event_text),
                    fallback_target_code,
                    fallback_target_names,
                ),
            )
        )

    return events
