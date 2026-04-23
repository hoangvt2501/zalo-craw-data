export default function Sidebar({
  activePage,
  hotelCount,
  unmatchedCount,
  fileStatus,
  language,
  theme,
  onToggleLanguage,
  onToggleTheme,
  onReloadLive,
  onPageChange,
  onFileSelected,
}) {
  const isEnglish = language === "en";

  return (
    <aside className="sidebar">
      <div className="s-head">
        <div className="s-brand">Hotel Intel</div>
        <div className="s-tagline">Zalo Monitor</div>
      </div>

      <nav className="s-nav">
        <button type="button" className={`s-item ${activePage === "deals" ? "active" : ""}`} onClick={() => onPageChange("deals")}>
          <span className="s-ico">◇</span>
          <span>{isEnglish ? "Deals" : "Deals"}</span>
          <span className="s-num">{hotelCount}</span>
        </button>

        <button type="button" className={`s-item ${activePage === "locations" ? "active" : ""}`} onClick={() => onPageChange("locations")}>
          <span className="s-ico">◎</span>
          <span>{isEnglish ? "Locations" : "Địa điểm"}</span>
        </button>

        <button type="button" className={`s-item ${activePage === "senders" ? "active" : ""}`} onClick={() => onPageChange("senders")}>
          <span className="s-ico">◉</span>
          <span>{isEnglish ? "Senders" : "Người gửi"}</span>
        </button>

        <div className="s-sep" />

        <button type="button" className={`s-item ${activePage === "unmatched" ? "active" : ""}`} onClick={() => onPageChange("unmatched")}>
          <span className="s-ico">△</span>
          <span>{isEnglish ? "Rejected " : "Không phải khách sạn"}</span>
          <span className="s-num warn">{unmatchedCount}</span>
        </button>
      </nav>

      <div className="s-foot">
        <div className="s-toggles" style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
          <button
            type="button"
            className="s-toggle-btn"
            onClick={() => onToggleTheme(theme === "night" ? "paper" : "night")}
            style={{ flex: 1, padding: "6px", background: "var(--bg3)", border: "1px solid var(--line)", borderRadius: "6px", color: "var(--text)", cursor: "pointer", fontSize: "11px", fontFamily: "Geist Mono, monospace" }}
          >
            {theme === "night" ? "🌙 Dark" : "☀️ Light"}
          </button>

          <button
            type="button"
            className="s-toggle-btn"
            onClick={() => onToggleLanguage(language === "vi" ? "en" : "vi")}
            style={{ flex: 1, padding: "6px", background: "var(--bg3)", border: "1px solid var(--line)", borderRadius: "6px", color: "var(--text)", cursor: "pointer", fontSize: "11px", fontFamily: "Geist Mono, monospace" }}
          >
            {language === "vi" ? "🇻🇳 VI" : "🇺🇸 EN"}
          </button>
        </div>

        <label className="s-upload">
          {isEnglish ? "Load hotels.jsonl" : "Load hotels.jsonl"}
          <input type="file" accept=".json,.jsonl" onChange={onFileSelected} hidden />
        </label>

        <div className="s-fstatus">{fileStatus}</div>

        <button type="button" className="s-reload" onClick={onReloadLive}>
          {isEnglish ? "Reload live API" : "Tải lại live API"}
        </button>
      </div>
    </aside>
  );
}
