import { formatDate } from "../lib/dashboard-utils";

const reasonMapEn = {
  filter_no_hotel_keywords: "No hotel keywords",
  filter_tour_only: "Tour or transportation",
  filter_per_person_only: "Price per person (tour/package)",
  filter_no_price: "No price found",
  filter_too_short: "Message too short",
  no_hotel_keywords: "No hotel keywords",
  tour_only: "Tour or transportation",
  per_person_only: "Price per person (tour/package)",
  no_price: "No price found",
  too_short: "Message too short",
  extract_no_hotels: "No hotel info extracted",
  rule_no_property_match: "Property not found in DB",
  llm_property_match_false: "AI rejected property match",
  rule_score_below_llm_min: "Match score too low",
};

const reasonMapVi = {
  filter_no_hotel_keywords: "Không chứa từ khóa khách sạn",
  filter_tour_only: "Nội dung tour / vận chuyển",
  filter_per_person_only: "Báo giá theo đầu người (tour)",
  filter_no_price: "Không tìm thấy giá",
  filter_too_short: "Tin nhắn quá ngắn",
  no_hotel_keywords: "Không chứa từ khóa khách sạn",
  tour_only: "Nội dung tour / vận chuyển",
  per_person_only: "Báo giá theo đầu người (tour)",
  no_price: "Không tìm thấy giá",
  too_short: "Tin nhắn quá ngắn",
  extract_no_hotels: "Không trích xuất được thông tin KS",
  rule_no_property_match: "Không tìm thấy khách sạn trong DB",
  llm_property_match_false: "AI xác nhận không phải KS này",
  rule_score_below_llm_min: "Điểm khớp quá thấp",
};

function formatReason(reason, isEnglish) {
  if (!reason) return isEnglish ? "Unknown reason" : "Lý do không xác định";
  const map = isEnglish ? reasonMapEn : reasonMapVi;
  return map[reason] || reason.replace(/_/g, " ");
}

export default function UnmatchedView({ language, records, onOpenDetail }) {
  const isEnglish = language === "en";

  return (
    <section>
      <div className="ph">
        <div className="ph-left">
          <h1>{isEnglish ? "Rejected " : "Bị từ chối "}<em>{isEnglish ? "non-hotel rows" : "không phải khách sạn"}</em></h1>
          <p>
            {isEnglish
              ? "Only rows that are not hotel content are shown here."
              : "Chỉ hiển thị các dòng không đúng nội dung khách sạn."}
          </p>
        </div>
      </div>

      <div className="tcard">
        <div className="tscroll">
          <table className="flat">
            <thead>
              <tr>
                <th>{isEnglish ? "Name in message" : "Tên trong message"}</th>
                <th>{isEnglish ? "Reject reason" : "Lý do từ chối"}</th>
                <th>{isEnglish ? "Sender" : "Người gửi"}</th>
                <th>{isEnglish ? "Date" : "Ngày"}</th>
              </tr>
            </thead>
            <tbody>
              {records.length ? records.map((record) => (
                <tr key={record.hotel_id || record.raw_message_id} onClick={() => onOpenDetail(record)}>
                  <td><div className="t-hotel">{record.hotel_name || "-"}</div></td>
                  <td style={{ color: "var(--red)", fontWeight: 500, fontSize: "12px" }}>
                    {formatReason(record.reject_reason, isEnglish)}
                  </td>
                  <td className="muted-cell">{record.sender_name || "-"}</td>
                  <td className="muted-cell">{formatDate(record.msg_sent_at, language)}</td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={4} className="empty-table">
                    {isEnglish ? "No non-hotel rejected records." : "Không có bản ghi non-hotel bị loại."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
