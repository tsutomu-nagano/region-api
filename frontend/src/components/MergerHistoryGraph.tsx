import type { Merger, MunicipalityRef } from "../types";

type MergerHistoryGraphProps = {
  mergers: Merger[];
  municipalityCode?: string;
};

const STATUS_CHANGE_TYPES = new Set(["special_city", "core_city"]);

function displayName(merger: Merger): string {
  return merger.municipality_name || merger.district_name || merger.prefecture_name;
}

function fallbackTarget(merger: Merger): MunicipalityRef {
  return {
    code: merger.code,
    name: displayName(merger),
    code_inferred: false,
  };
}

function refText(ref: MunicipalityRef): string {
  return ref.code ? `${ref.name} ${ref.code}` : ref.name;
}

function isStatusChange(merger: Merger): boolean {
  return STATUS_CHANGE_TYPES.has(merger.reason_events[0]?.type || "");
}

function eventLabel(merger: Merger): string {
  const label = merger.reason_events[0]?.label;
  if (label) {
    return label;
  }
  return isStatusChange(merger) ? "都市種別変更" : "廃置分合";
}

export function MergerHistoryGraph({ mergers, municipalityCode }: MergerHistoryGraphProps) {
  const sortedMergers = [...mergers].sort((a, b) =>
    (a.effective_date || "").localeCompare(b.effective_date || ""),
  );

  if (sortedMergers.length === 0) {
    return (
      <section className="history-empty" aria-label="廃置分合履歴">
        <p>該当する廃置分合履歴はありません。</p>
      </section>
    );
  }

  return (
    <section className="timeline-panel" aria-label="廃置分合履歴">
      <div className="timeline-panel-header">
        <div>
          <p className="eyebrow">Timeline</p>
          <h3>{municipalityCode ? `${municipalityCode} の変更履歴` : "変更履歴"}</h3>
        </div>
        <div className="timeline-legend" aria-label="凡例">
          <span><i className="legend-dot is-merger" />合併・編入</span>
          <span><i className="legend-dot is-status" />都市種別変更</span>
        </div>
      </div>

      <ol className="timeline-list">
        {sortedMergers.map((merger) => {
          const event = merger.reason_events[0];
          const statusChange = isStatusChange(merger);
          const sources = statusChange ? [] : event?.source_municipalities || [];
          const targets = statusChange ? [] : event?.target_municipalities.length ? event.target_municipalities : [fallbackTarget(merger)];

          return (
            <li className={`timeline-event${statusChange ? " is-status-change" : ""}`} key={merger.id}>
              <div className="timeline-stem" aria-hidden="true">
                <span className="timeline-marker" />
              </div>

              <article className="timeline-card">
                <div className="timeline-card-top">
                  <time>{merger.effective_date || "施行日不明"}</time>
                  <span className="event-pill">{statusChange ? "都市種別変更" : eventLabel(merger)}</span>
                </div>

                <h4>{displayName(merger)}</h4>
                <p>{merger.reason}</p>

                {!statusChange && (
                  <div className="municipality-flow" aria-label="変更元と変更先">
                    <div className="municipality-chip-group">
                      {sources.length ? (
                        sources.map((ref) => (
                          <span className="municipality-chip" key={`source-${merger.id}-${ref.code || ref.name}`}>
                            <small>変更元</small>
                            {refText(ref)}
                          </span>
                        ))
                      ) : (
                        <span className="municipality-chip is-muted">
                          <small>変更元</small>
                          記載なし
                        </span>
                      )}
                    </div>

                    <span className="flow-arrow" aria-hidden="true">→</span>

                    <div className="municipality-chip-group">
                      {targets.map((ref) => (
                        <span className="municipality-chip is-target" key={`target-${merger.id}-${ref.code || ref.name}`}>
                          <small>変更先</small>
                          {refText(ref)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </article>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
