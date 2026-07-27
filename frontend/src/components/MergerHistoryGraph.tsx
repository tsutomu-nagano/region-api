import type { Merger, MunicipalityRef } from "../types";

type MergerHistoryGraphProps = {
  mergers: Merger[];
  municipalityCode?: string;
};

const EVENT_COLORS: Record<string, string> = {
  merge_new: "#0f766e",
  absorption: "#2563eb",
  new_establishment: "#0891b2",
  split: "#c2410c",
  city_status: "#7c3aed",
  town_status: "#9333ea",
  rename: "#be123c",
  designated_city: "#047857",
  core_city: "#0369a1",
  special_city: "#4f46e5",
};

function displayName(merger: Merger): string {
  return merger.municipality_name || merger.district_name || merger.prefecture_name;
}

function refLabel(ref: MunicipalityRef): string {
  return ref.code ? `${ref.name} (${ref.code})` : ref.name;
}

function refsLabel(refs: MunicipalityRef[], emptyLabel: string): string {
  if (refs.length === 0) {
    return emptyLabel;
  }
  return refs.map(refLabel).join("、");
}

function eventColor(merger: Merger): string {
  return EVENT_COLORS[merger.reason_events[0]?.type || ""] || "#475569";
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

  const width = 960;
  const rowHeight = 112;
  const topPadding = 40;
  const bottomPadding = 40;
  const height = topPadding + bottomPadding + Math.max(1, sortedMergers.length - 1) * rowHeight;
  const centerX = width / 2;

  return (
    <section className="history-graph" aria-label="廃置分合履歴">
      <div className="graph-header">
        <div>
          <p className="eyebrow">Merger History</p>
          <h2>{municipalityCode ? `${municipalityCode} の廃置分合履歴` : "廃置分合履歴"}</h2>
        </div>
        <p className="history-count">{sortedMergers.length.toLocaleString("ja-JP")}件</p>
      </div>

      <div className="timeline" role="list">
        <svg viewBox={`0 0 ${width} ${height}`} className="timeline-svg" aria-hidden="true">
          <line x1={centerX} y1={topPadding} x2={centerX} y2={height - bottomPadding} className="timeline-line" />
          {sortedMergers.map((merger, index) => {
            const y = topPadding + index * rowHeight;
            const color = eventColor(merger);
            return (
              <g key={merger.id}>
                <circle cx={centerX} cy={y} r="10" fill={color} />
                <line x1={centerX - 10} y1={y} x2={index % 2 === 0 ? 252 : 708} y2={y} stroke={color} strokeWidth="2" />
              </g>
            );
          })}
        </svg>

        <div className="timeline-items">
          {sortedMergers.map((merger, index) => {
            const event = merger.reason_events[0];
            const y = topPadding + index * rowHeight;
            const sideClass = index % 2 === 0 ? "is-left" : "is-right";
            return (
              <article
                className={`history-card ${sideClass}`}
                key={merger.id}
                role="listitem"
                style={{ top: `${y}px`, borderColor: eventColor(merger) }}
              >
                <div className="card-topline">
                  <time>{merger.effective_date || "施行日不明"}</time>
                  <span>{event?.label || "その他"}</span>
                </div>
                <h3>{displayName(merger)}</h3>
                <dl>
                  <div>
                    <dt>変更元</dt>
                    <dd>{refsLabel(event?.source_municipalities || [], "記載なし")}</dd>
                  </div>
                  <div>
                    <dt>変更先</dt>
                    <dd>{refsLabel(event?.target_municipalities || [], `${displayName(merger)} (${merger.code})`)}</dd>
                  </div>
                </dl>
                <p>{merger.reason}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
