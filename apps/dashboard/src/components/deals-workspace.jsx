import { useEffect, useState } from "react";
import {
  formatDateTime,
  formatCompact,
  formatCurrency,
  getContact,
  getMinPrice,
} from "../lib/dashboard-utils";

function Kpi({ tone, label, value, sublabel }) {
  return (
    <div className={`kpi ${tone}`}>
      <div className="kpi-l">{label}</div>
      <div className="kpi-v">{value}</div>
      <div className="kpi-s">{sublabel}</div>
    </div>
  );
}

function summarizeServices(record) {
  const services = (record.extra_services || []).filter(Boolean);
  if (!services.length) {
    return "-";
  }
  if (services.length <= 2) {
    return services.join(", ");
  }
  return `${services.slice(0, 2).join(", ")}...`;
}

function GroupedView({
  language,
  groupedEntries,
  expandedKeys,
  compareKeys,
  onToggleExpanded,
  onToggleCompare,
  onOpenDetail,
}) {
  const isEnglish = language === "en";

  return (
    <div className="group-list">
      {groupedEntries.map(([key, offers]) => {
        const lead = offers[0];
        const bestPrice = getMinPrice(lead);
        const worstPrice = Math.max(...offers.map((offer) => getMinPrice(offer) || 0));
        const isExpanded = expandedKeys.includes(key);
        const compareSelected = compareKeys.includes(key);
        const isUnmatched = lead.matched === false;
        const priceDelta = bestPrice && worstPrice && worstPrice > bestPrice
          ? Math.round(((worstPrice - bestPrice) / bestPrice) * 100)
          : 0;
        const locStr = lead.location_sub && lead.location_sub !== lead.location
          ? `${lead.location_sub}, ${lead.location}`
          : (lead.location || "-");
        const scoreStr = lead.match_score != null
          ? `${Math.round(Number(lead.match_score) * 100)}%`
          : null;

        return (
          <article
            key={key}
            className={`group-card ${isExpanded ? "expanded" : ""} ${isUnmatched ? "unmatched-hotel" : ""}`}
          >
            <div className="group-head" onClick={() => onToggleExpanded(key)}>
              <div className="gh-name">
                <div className="gh-title">{lead.property_name || lead.hotel_name || "-"}</div>
                <div className="gh-loc">📍 {locStr}</div>
                {lead.matched && lead.property_name ? (
                  <div className="gh-prop">
                    ↳ {lead.hotel_name || lead.property_name}
                    {scoreStr ? ` | ${scoreStr}` : ""}
                  </div>
                ) : (
                  <div className="gh-unmatched">
                    ✕ {isEnglish ? "Not matched with DB" : "Chưa khớp DB"}
                    <span className="unmatched-pill">{isEnglish ? "UNMATCHED" : "CHƯA KHỚP"}</span>
                  </div>
                )}
              </div>

              {lead.stars
                ? <span className="star-b">★ {lead.stars}</span>
                : <span className="star-b muted">?★</span>}

              <div className={`offers-badge ${offers.length > 1 ? "multi" : ""}`}>
                {offers.length} {isEnglish ? "offer" : "offer"}{offers.length > 1 ? "s" : ""}
              </div>

              <div className="price-best">
                <div className="price-best-val">{isEnglish ? "from" : "từ"} {formatCompact(bestPrice, language)}đ</div>
                <div className="price-best-lbl">
                  {offers.length > 1
                    ? (isEnglish ? "best price" : "giá tốt nhất")
                    : (isEnglish ? "listed" : "niêm yết")}
                </div>
              </div>

              {worstPrice && worstPrice !== bestPrice ? (
                <div className="price-range">
                  <div className="price-range-val">{formatCompact(bestPrice, language)}-{formatCompact(worstPrice, language)}</div>
                  <div style={{ fontSize: "10px", color: "var(--muted)", marginTop: "1px" }}>
                    {isEnglish ? "price spread" : "độ chênh giá"}
                  </div>
                </div>
              ) : <div />}

              <div className={`delta-badge ${priceDelta ? "up" : "eq"}`}>
                {priceDelta ? `+${priceDelta}%` : (isEnglish ? "flat" : "đồng giá")}
              </div>

              <div className="group-right">
                <button
                  type="button"
                  className={`cmp-btn ${compareSelected ? "selected" : ""}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    onToggleCompare(key);
                  }}
                  title={compareSelected ? (isEnglish ? "Remove" : "Bỏ chọn") : (isEnglish ? "Compare" : "So sánh")}
                >
                  {compareSelected ? `✓ ${isEnglish ? "Comparing" : "Đang so sánh"}` : `+ ${isEnglish ? "Compare" : "So sánh"}`}
                </button>
                <span className="expand-ico">{isExpanded ? "▲" : "▼"}</span>
              </div>
            </div>

            <div className="offers-wrap">
              <div className="offers-inner">
                <table className="offers-table">
                  <thead>
                    <tr>
                      <th>{isEnglish ? "Sender" : "Người gửi"}</th>
                      <th>{isEnglish ? "Group" : "Nhóm"}</th>
                      <th>{isEnglish ? "Room · Price" : "Loại phòng · Giá"}</th>
                      <th>{isEnglish ? "Breakfast" : "Bữa sáng"}</th>
                      <th>{isEnglish ? "Dates" : "Ngày trống"}</th>
                      <th>{isEnglish ? "Contact" : "Liên hệ"}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {offers.map((offer, index) => {
                      const price = getMinPrice(offer);
                      const isBest = index === 0 && offers.length > 1;
                      const roomTypes = offer.room_types || [];
                      const bestReference = getMinPrice(offers[0]);

                      return (
                        <tr
                          key={offer.hotel_id || `${key}-${index}`}
                          className={`${isBest ? "best-offer " : ""}clickable-row ${offer.matched === false ? "unmatched-row" : ""}`}
                          onClick={() => onOpenDetail(offer)}
                        >
                          <td>
                            <div className="sender-name">
                              {offer.sender_name || "-"}
                              {isBest ? <span className="winner-chip">BEST</span> : null}
                            </div>
                            <div className="sender-co">{offer.contact_company || ""}</div>
                          </td>
                          <td style={{ fontSize: "11.5px", color: "var(--muted)" }}>{offer.group_name || "-"}</td>
                          <td>
                            {roomTypes.length > 0 ? (
                              roomTypes.map((roomType, roomIndex) => (
                                <div
                                  key={`${offer.hotel_id || index}-${roomIndex}`}
                                  style={{ display: "flex", alignItems: "baseline", gap: "6px", marginBottom: "3px" }}
                                >
                                  <span style={{ fontSize: "11.5px", color: "var(--muted)" }}>{roomType.name}</span>
                                  <span className={`offer-price ${isBest ? "best" : ""}`}>{formatCompact(roomType.price_vnd, language)}đ</span>
                                  <span style={{ fontSize: "10px", color: "var(--muted2)" }}>
                                    /{roomType.price_per || (isEnglish ? "night" : "đêm")}
                                  </span>
                                  {roomType.quantity ? <span className="qty-highlight">×{roomType.quantity}</span> : null}
                                </div>
                              ))
                            ) : (
                              <span className={`offer-price ${isBest ? "best" : ""}`}>{formatCurrency(price, language)}</span>
                            )}
                            {!isBest && price && bestReference && price > bestReference ? (
                              <div className="offer-delta worse">
                                +{Math.round(((price - bestReference) / bestReference) * 100)}%
                              </div>
                            ) : null}
                            {isBest ? <div className="offer-delta best">{isEnglish ? "Best price" : "Giá tốt nhất"}</div> : null}
                          </td>
                          <td>
                            {offer.includes_breakfast === true ? (
                              <span className="bfast-y">{isEnglish ? "yes" : "có"}</span>
                            ) : offer.includes_breakfast === false ? (
                              <span className="bfast-n">{isEnglish ? "no" : "không"}</span>
                            ) : (
                              <span className="bfast-n">-</span>
                            )}
                          </td>
                          <td style={{ whiteSpace: "nowrap" }}>
                            <div className="date-chip-wrap">
                              {(offer.checkin_dates || []).slice(0, 4).map((date) => (
                                <span key={`${offer.hotel_id || index}-${date}`} className="date-chip">{date}</span>
                              ))}
                              {(offer.checkin_dates || []).length > 4
                                ? <span className="date-chip">+{offer.checkin_dates.length - 4}</span>
                                : null}
                            </div>
                          </td>
                          <td><div className="contact-val">{getContact(offer)}</div></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}

function FlatView({ language, flatRecords, flatSort, onChangeFlatSort, compareKeys, onToggleCompare, onOpenDetail }) {
  const isEnglish = language === "en";

  function nextDirection(column) {
    if (flatSort.column !== column) {
      return 1;
    }
    return flatSort.dir * -1;
  }

  if (!flatRecords.length) {
    return (
      <div className="tcard">
        <div className="empty-table">{isEnglish ? "No result" : "Không có kết quả"}</div>
      </div>
    );
  }

  return (
    <div className="tcard">
      <div className="tscroll">
        <table className="flat">
          <thead>
            <tr>
              <th>{isEnglish ? "Hotel" : "Khách sạn"}</th>
              <th>{isEnglish ? "Stars" : "Sao"}</th>
              <th>
                <button type="button" className="tableSort" onClick={() => onChangeFlatSort("price", nextDirection("price"))}>
                  {isEnglish ? "Price" : "Giá"} ^
                </button>
              </th>
              <th>{isEnglish ? "Dates" : "Ngày trống"}</th>
              <th>{isEnglish ? "Services" : "Dịch vụ"}</th>
              <th>
                <button type="button" className="tableSort" onClick={() => onChangeFlatSort("sender_name", nextDirection("sender_name"))}>
                  {isEnglish ? "Sender" : "Người gửi"} ^
                </button>
              </th>
              <th>{isEnglish ? "Compare" : "So sánh"}</th>
            </tr>
          </thead>
          <tbody>
            {flatRecords.map((record) => {
              const key = record.matched && record.property_id
                ? `property:${record.property_id}`
                : `raw:${String(record.hotel_name || "").toLowerCase().replace(/\s+/g, "-")}`;
              const compareSelected = compareKeys.includes(key);
              const isUnmatchedRow = record.matched === false;

              return (
                <tr key={record.hotel_id} className={isUnmatchedRow ? "unmatched-row" : ""} onClick={() => onOpenDetail(record)}>
                  <td>
                    <div className="t-hotel">{record.hotel_name || "-"}</div>
                    <div className="t-loc">{record.location_sub || record.location || "-"}</div>
                    {record.property_name ? (
                      <div className="t-prop">{record.property_name}</div>
                    ) : isUnmatchedRow ? (
                      <div className="t-prop unmatched-label">{isEnglish ? "Unmatched with DB" : "Chưa khớp DB"}</div>
                    ) : null}
                  </td>
                  <td>{record.stars ? <span className="star-b">{record.stars}*</span> : <span className="muted-inline">-</span>}</td>
                  <td className="mono-strong">{formatCurrency(getMinPrice(record), language)}</td>
                  <td>
                    {(record.checkin_dates || []).slice(0, 3).map((date) => (
                      <span key={`${record.hotel_id}-${date}`} className="date-chip">{date}</span>
                    ))}
                  </td>
                  <td className="muted-cell">{summarizeServices(record)}</td>
                  <td className="muted-cell">{record.sender_name || "-"}</td>
                  <td>
                    <button
                      type="button"
                      className={`cmp-btn ${compareSelected ? "selected" : ""}`}
                      onClick={(event) => {
                        event.stopPropagation();
                        onToggleCompare(key);
                      }}
                    >
                      {compareSelected ? "✓" : "+ Compare"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function DealsWorkspace({
  filters,
  kpis,
  groupedEntries,
  flatRecords,
  locationOptions,
  metricsSummary,
  language,
  view,
  expandedKeys,
  flatSort,
  compareKeys,
  onViewChange,
  onFilterChange,
  onClearFilters,
  onToggleExpanded,
  onChangeFlatSort,
  onToggleCompare,
  onOpenDetail,
}) {
  const isEnglish = language === "en";
  const totalGroups = groupedEntries.length;
  const lastUpdatedLabel = kpis.lastUpdated ? formatDateTime(kpis.lastUpdated, language) : "-";

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  useEffect(() => {
    setPage(1);
  }, [filters, view, language, flatSort]);

  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;

  const currentGroupedEntries = view === "group" ? groupedEntries.slice(startIndex, endIndex) : [];
  const currentFlatRecords = view === "flat" ? flatRecords.slice(startIndex, endIndex) : [];
  const totalItems = view === "group" ? totalGroups : flatRecords.length;
  const totalPages = Math.ceil(totalItems / pageSize) || 1;
  const unmatchedHotelsCount = flatRecords.filter((record) => record.matched === false).length;
  const matchedHotelsCount = flatRecords.length - unmatchedHotelsCount;

  return (
    <section>
      <div className="ph">
        <div className="ph-left">
          <h1>{isEnglish ? "Hotel " : "Hotel "}<em>{isEnglish ? "deals" : "deals"}</em></h1>
          <p>
            {lastUpdatedLabel}
            {metricsSummary ? ` | DB ${metricsSummary.hotel_deals} matched` : ""}
            {` | ${unmatchedHotelsCount} ${isEnglish ? "unmatched" : "chưa khớp"}`}
          </p>
        </div>
        <div className="ph-right">
          <div className="vtoggle">
            <button type="button" className={`vbtn ${view === "group" ? "active" : ""}`} onClick={() => onViewChange("group")}>Grouped</button>
            <button type="button" className={`vbtn ${view === "flat" ? "active" : ""}`} onClick={() => onViewChange("flat")}>Flat</button>
          </div>
          <div className="pill">
            {matchedHotelsCount} {isEnglish ? "matched" : "khớp DB"} / {unmatchedHotelsCount} {isEnglish ? "unmatched" : "chưa khớp"}
          </div>
        </div>
      </div>

      <div className="kpi-strip">
        <Kpi tone="k1" label={isEnglish ? "Unique hotels" : "KS unique"} value={kpis.uniqueHotels} sublabel={isEnglish ? "grouped properties" : "nhóm khách sạn"} />
        <Kpi tone="k2" label={isEnglish ? "Offers" : "Tổng offers"} value={kpis.offers} sublabel={isEnglish ? "visible rows" : "dòng hiển thị"} />
        <Kpi tone="k3" label={isEnglish ? "Best price" : "Giá tốt nhất"} value={formatCompact(kpis.bestPrice, language)} sublabel="VND" />
        <Kpi tone="k5" label={isEnglish ? "Senders" : "Người gửi"} value={kpis.senders} sublabel={`${kpis.companies} companies`} />
      </div>

      <div className="fbar">
        <span className="fbar-l">{isEnglish ? "Filter" : "Lọc"}</span>
        <div className="sw">
          <input
            className="finput"
            value={filters.query}
            onChange={(event) => onFilterChange("query", event.target.value)}
            placeholder={isEnglish ? "Hotel, location, contact..." : "Tên KS, địa điểm, liên hệ..."}
          />
        </div>

        <select className="fsel" value={filters.location} onChange={(event) => onFilterChange("location", event.target.value)}>
          <option value="">{isEnglish ? "All locations" : "Tất cả tỉnh"}</option>
          {locationOptions.map((location) => (
            <option key={location} value={location}>{location}</option>
          ))}
        </select>

        <select className="fsel" value={filters.stars} onChange={(event) => onFilterChange("stars", event.target.value)}>
          <option value="">{isEnglish ? "All stars" : "Tất cả sao"}</option>
          <option value="5">5*</option>
          <option value="4">4*</option>
          <option value="3">3*</option>
          <option value="0">?*</option>
        </select>

        <select className="fsel" value={filters.price} onChange={(event) => onFilterChange("price", event.target.value)}>
          <option value="">{isEnglish ? "All prices" : "Tất cả giá"}</option>
          <option value="0-1000000">{isEnglish ? "Under 1m" : "Dưới 1tr"}</option>
          <option value="1000000-2000000">1-2tr</option>
          <option value="2000000-5000000">2-5tr</option>
          <option value="5000000-99999999">{isEnglish ? "Above 5m" : "Trên 5tr"}</option>
        </select>

        <select className="fsel" value={filters.sort} onChange={(event) => onFilterChange("sort", event.target.value)}>
          <option value="price_a">{isEnglish ? "Best price first" : "Giá tốt nhất trước"}</option>
          <option value="offers_d">{isEnglish ? "Most offers" : "Nhiều offer nhất"}</option>
          <option value="date_d">{isEnglish ? "Newest" : "Mới nhất"}</option>
          <option value="stars_d">{isEnglish ? "Top stars" : "Sao cao nhất"}</option>
        </select>

        <button type="button" className="fbtn" onClick={onClearFilters}>x</button>
        <span className="fcount"><b>{totalGroups}</b> {isEnglish ? "hotels" : "khách sạn"}</span>
      </div>

      {view === "group" ? (
        <GroupedView
          language={language}
          groupedEntries={currentGroupedEntries}
          expandedKeys={expandedKeys}
          compareKeys={compareKeys}
          onToggleExpanded={onToggleExpanded}
          onToggleCompare={onToggleCompare}
          onOpenDetail={onOpenDetail}
        />
      ) : (
        <FlatView
          language={language}
          flatRecords={currentFlatRecords}
          flatSort={flatSort}
          onChangeFlatSort={onChangeFlatSort}
          compareKeys={compareKeys}
          onToggleCompare={onToggleCompare}
          onOpenDetail={onOpenDetail}
        />
      )}

      {totalItems > 0 ? (
        <div
          className="pagination-bar"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "24px",
            padding: "16px",
            background: "var(--bg2)",
            borderRadius: "12px",
            border: "1px solid var(--line)",
          }}
        >
          <div className="page-size-selector" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "13px", color: "var(--muted)" }}>{isEnglish ? "Show:" : "Hiển thị:"}</span>
            <select
              value={pageSize}
              onChange={(event) => {
                setPageSize(Number(event.target.value));
                setPage(1);
              }}
              style={{
                background: "var(--bg3)",
                border: "1px solid var(--line)",
                color: "var(--text)",
                padding: "4px 8px",
                borderRadius: "6px",
                fontSize: "13px",
              }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>

          <div className="page-controls" style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <button
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page === 1}
              style={{
                background: page === 1 ? "transparent" : "var(--bg3)",
                border: "1px solid var(--line)",
                color: page === 1 ? "var(--muted)" : "var(--text)",
                padding: "6px 12px",
                borderRadius: "6px",
                cursor: page === 1 ? "not-allowed" : "pointer",
              }}
            >
              {isEnglish ? "Prev" : "Trước"}
            </button>
            <span style={{ fontSize: "13px", color: "var(--text)" }}>
              {isEnglish ? "Page" : "Trang"} <b>{page}</b> / {totalPages}
            </span>
            <button
              onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              disabled={page === totalPages}
              style={{
                background: page === totalPages ? "transparent" : "var(--bg3)",
                border: "1px solid var(--line)",
                color: page === totalPages ? "var(--muted)" : "var(--text)",
                padding: "6px 12px",
                borderRadius: "6px",
                cursor: page === totalPages ? "not-allowed" : "pointer",
              }}
            >
              {isEnglish ? "Next" : "Sau"}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
