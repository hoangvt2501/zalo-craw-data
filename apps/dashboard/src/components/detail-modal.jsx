import { formatCurrency, formatDateTime, getContact, getMaxPrice, getMinPrice } from "../lib/dashboard-utils";

function MetaField({ label, value }) {
  return (
    <div className="mf">
      <div className="mf-l">{label}</div>
      <div className="mf-v">{value || "-"}</div>
    </div>
  );
}

export default function DetailModal({ language, open, record, detail, loading, error, onClose }) {
  if (!record) {
    return null;
  }

  const isEnglish = language === "en";
  const resolvedRecord = detail?.deal || record;
  const message = detail?.message || null;
  const rawMessage = resolvedRecord.raw_text || message?.text || record.raw_text || null;
  const rooms = detail?.rooms || [];
  const extraServices = resolvedRecord.extra_services || [];
  const checkinDates = resolvedRecord.checkin_dates || [];
  const stars = resolvedRecord.stars;
  const locStr = resolvedRecord.location_sub && resolvedRecord.location_sub !== resolvedRecord.location
    ? `${resolvedRecord.location_sub}, ${resolvedRecord.location}`
    : (resolvedRecord.location_sub || resolvedRecord.location || "—");
  const starsStr = stars ? " · " + "★".repeat(stars) : "";

  return (
    <div
      className={`overlay ${open ? "open" : ""}`}
      onClick={onClose}
      aria-hidden={open ? "false" : "true"}
    >
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <div className="m-head">
          <div className="m-head-content">
            <div className="m-name">{resolvedRecord.property_name || resolvedRecord.hotel_name || "—"}</div>
            <div className="m-loc">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle>
              </svg>
              {locStr}{starsStr}
              {resolvedRecord.matched && resolvedRecord.hotel_name && resolvedRecord.hotel_name !== resolvedRecord.property_name
                ? <span className="m-alias">↳ {isEnglish ? "In message" : "Trong tin"}: “{resolvedRecord.hotel_name}”</span>
                : null}
            </div>
          </div>
          <button type="button" className="m-close" onClick={onClose}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div className="m-body">
          {/* Meta fields */}
          <div className="m-grid">
            <MetaField label={isEnglish ? "Sender" : "Người gửi"} value={resolvedRecord.sender_name} />
            <MetaField label={isEnglish ? "Company" : "Công ty"} value={resolvedRecord.contact_company} />
            <MetaField label={isEnglish ? "Contact" : "Liên hệ"} value={getContact(resolvedRecord)} />
          </div>

          {/* Room Types Table */}
          {rooms.length > 0 && (
            <div style={{marginBottom:"24px"}}>
              <div className="m-sec-title">{isEnglish ? "Room Types & Prices" : "Loại phòng & Giá"}</div>
              <div className="m-table-wrap">
                <table className="m-rooms-table">
                  <thead>
                    <tr>
                      {[isEnglish?"Type":"Loại", isEnglish?"Qty":"SL", isEnglish?"Price":"Giá", isEnglish?"Per":"Tính theo", isEnglish?"Breakfast":"Sáng"].map(h => (
                        <th key={h}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rooms.map((room, i) => {
                      const raw = room.raw_payload || {};
                      return (
                        <tr key={i}>
                          <td className="room-name-cell">{room.name || (isEnglish ? "Standard" : "Tiêu chuẩn")}</td>
                          <td>{room.quantity ? <span className="qty-highlight large">×{room.quantity}</span> : "—"}</td>
                          <td className="price-cell">{room.price_vnd ? `${formatCurrency(room.price_vnd, language)}` : "—"}</td>
                          <td className="per-cell">{room.price_per || (isEnglish ? "night" : "đêm")}</td>
                          <td>{raw.includes_breakfast === true ? "✓" : raw.includes_breakfast === false ? "✗" : "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Check-in Dates */}
          {checkinDates.length > 0 && (
            <div style={{marginBottom:"24px"}}>
              <div className="m-sec-title">{isEnglish ? "Available Dates" : "Ngày còn phòng"}</div>
              <div className="date-chip-wrap">
                {checkinDates.map(d => <span key={d} className="date-chip">{d}</span>)}
              </div>
            </div>
          )}

          {/* Extra Services */}
          {extraServices.length > 0 && (
            <div style={{marginBottom:"24px"}}>
              <div className="m-sec-title">{isEnglish ? "Services" : "Dịch vụ"}</div>
              <div className="svc-chip-wrap">
                {extraServices.map(s => (
                  <span key={s} className="svc-chip">✓ {s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Original Message */}
          <div className="m-msg-wrap">
            <div className="m-sec-title">{isEnglish ? "Original message" : "Nội dung message gốc"}</div>
            <div className="message-box">
              {loading ? "Đang tải..." : error ? <span className="error">{error}</span> : rawMessage || (isEnglish ? "No message content." : "Không có nội dung message.")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
