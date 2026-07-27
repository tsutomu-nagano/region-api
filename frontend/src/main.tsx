import { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { MergerHistoryGraph } from "./components/MergerHistoryGraph";
import type { Merger } from "./types";
import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
    return {
      first: dated[0]?.effective_date || "-",
      last: dated[dated.length - 1]?.effective_date || "-",
      prefecture: mergers[0]?.prefecture_name || "-",
      name: mergers[mergers.length - 1]
        ? mergers[mergers.length - 1].municipality_name || mergers[mergers.length - 1].district_name || "-"
        : "-",
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
    <main>
      <section className="app-shell">
        <header className="page-header">
          <div>
            <p className="eyebrow">Region API Sample</p>
            <h1>廃置分合履歴ビューア</h1>
          </div>
          <form className="search-form" onSubmit={handleSubmit}>
            <label htmlFor="municipality-code">標準地域コード</label>
            <div>
              <input
                id="municipality-code"
                inputMode="numeric"
                pattern="[0-9]{5}"
                maxLength={5}
                value={codeInput}
                onChange={(event) => setCodeInput(event.target.value)}
              />
              <button type="submit">表示</button>
            </div>
          </form>
        </header>

        <section className="summary-grid" aria-label="概要">
          <div>
            <span>自治体</span>
            <strong>{summary.name}</strong>
          </div>
          <div>
            <span>都道府県</span>
            <strong>{summary.prefecture}</strong>
          </div>
          <div>
            <span>最初の履歴</span>
            <strong>{summary.first}</strong>
          </div>
          <div>
            <span>最新の履歴</span>
            <strong>{summary.last}</strong>
          </div>
        </section>

        {error && <p className="error-message">{error}</p>}
        {isLoading ? <p className="loading-message">読み込み中...</p> : <MergerHistoryGraph mergers={mergers} municipalityCode={selectedCode} />}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
