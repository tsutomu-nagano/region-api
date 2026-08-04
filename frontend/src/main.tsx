import { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { MergerHistoryGraph } from "./components/MergerHistoryGraph";
import type { Merger } from "./types";
import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const PREFECTURES = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "東京都", "大阪府", "福岡県"];

function App() {
  const [codeInput, setCodeInput] = useState("01202");
  const [selectedCode, setSelectedCode] = useState("01202");
  const [mergers, setMergers] = useState<Merger[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ code: selectedCode, limit: "1000" });

    setIsLoading(true);
    setError(null);

    fetch(`${API_BASE_URL}/api/v1/mergers?${params.toString()}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API request failed: ${response.status}`);
        }
        return response.json() as Promise<Merger[]>;
      })
      .then(setMergers)
      .catch((reason: unknown) => {
        if ((reason as Error).name !== "AbortError") {
          setError("廃置分合履歴を取得できませんでした。APIが起動しているか確認してください。");
        }
      })
      .finally(() => setIsLoading(false));

    return () => controller.abort();
  }, [selectedCode]);

  const summary = useMemo(() => {
    const dated = mergers.filter((merger) => merger.effective_date);
    const latest = mergers[mergers.length - 1];
    return {
      first: dated[0]?.effective_date || "-",
      last: dated[dated.length - 1]?.effective_date || "-",
      prefecture: latest?.prefecture_name || mergers[0]?.prefecture_name || "北海道",
      name: latest ? latest.municipality_name || latest.district_name || "-" : "函館市",
    };
  }, [mergers]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedCode = codeInput.trim();
    if (/^\d{5}$/.test(normalizedCode)) {
      setSelectedCode(normalizedCode);
    } else {
      setError("標準地域コードは5桁の数字で入力してください。");
    }
  }

  return (
    <main className="viewer-shell">
      <header className="viewer-topbar">
        <div className="brand-lockup">
          <img src="/assets/region-api-logo.jpg" alt="region api" className="brand-logo" />
          <div>
            <p className="eyebrow">Region API</p>
            <h1>廃置分合ビューア</h1>
          </div>
        </div>
        <span className="topbar-badge">updated from API</span>
      </header>

      <div className="viewer-layout">
        <aside className="viewer-sidebar" aria-label="検索条件">
          <form className="sidebar-search" onSubmit={handleSubmit}>
            <label htmlFor="municipality-code">自治体コード</label>
            <div className="search-row">
              <input
                id="municipality-code"
                inputMode="numeric"
                pattern="[0-9]{5}"
                maxLength={5}
                value={codeInput}
                onChange={(event) => setCodeInput(event.target.value)}
                placeholder="01202"
              />
              <button type="submit">表示</button>
            </div>
          </form>

          <label className="select-label" htmlFor="prefecture-select">都道府県</label>
          <select
            id="prefecture-select"
            className="prefecture-select"
            value={summary.prefecture}
            onChange={() => undefined}
            aria-label="都道府県"
          >
            {PREFECTURES.map((prefecture) => (
              <option key={prefecture}>{prefecture}</option>
            ))}
          </select>

          <section className="region-card" aria-label="選択中の自治体">
            <span className="region-card-label">選択中</span>
            <strong>{summary.name}</strong>
            <p>{selectedCode} / {summary.prefecture}</p>
          </section>

          <section className="sidebar-stats" aria-label="履歴概要">
            <div>
              <span>履歴件数</span>
              <strong>{mergers.length.toLocaleString("ja-JP")}</strong>
            </div>
            <div>
              <span>最初</span>
              <strong>{summary.first}</strong>
            </div>
            <div>
              <span>最新</span>
              <strong>{summary.last}</strong>
            </div>
          </section>
        </aside>

        <section className="viewer-content">
          <header className="content-header">
            <div>
              <p className="eyebrow">Municipality history</p>
              <h2>{summary.name}</h2>
              <p>{selectedCode} / {summary.prefecture}</p>
            </div>
            <div className="view-switch" aria-label="表示切替">
              <button type="button">系統図</button>
              <button type="button" className="is-active">時系列</button>
            </div>
          </header>

          {error && <p className="error-message">{error}</p>}
          {isLoading ? <p className="loading-message">読み込み中...</p> : <MergerHistoryGraph mergers={mergers} municipalityCode={selectedCode} />}
        </section>
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
