function trimBaseUrl(baseUrl) {
  return String(baseUrl || "/api").replace(/\/+$/, "");
}

async function fetchJson(url, signal) {
  const response = await fetch(url, {
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text.slice(0, 200)}`);
  }

  return response.json();
}

function ensureArray(value) {
  return Array.isArray(value) ? value : [];
}

const NON_HOTEL_REASONS = new Set([
  "filter_no_hotel_keywords",
  "filter_tour_only",
  "filter_per_person_only",
  "filter_no_price",
  "filter_too_short",
  "no_hotel_keywords",
  "tour_only",
  "per_person_only",
  "no_price",
  "too_short",
  "extract_no_hotels",
]);

function inferRejectBucket(reason) {
  if (NON_HOTEL_REASONS.has(reason)) {
    return "non_hotel";
  }
  return "hotel_unmatched";
}

function getRecordTimestamp(record) {
  const raw = record?.msg_sent_at;
  if (!raw) {
    return 0;
  }
  const ts = new Date(raw).getTime();
  return Number.isFinite(ts) ? ts : 0;
}

function mapDealItem(item) {
  const extracted = item.extracted_payload && typeof item.extracted_payload === "object"
    ? item.extracted_payload
    : {};

  return {
    hotel_id: item.id,
    raw_message_id: item.raw_message_id,
    hotel_name: item.hotel_name || extracted.hotel_name || item.property_name || "Unknown deal",
    stars: item.stars ?? extracted.stars ?? null,
    location: item.location || extracted.location || item.location_raw || "Unknown",
    location_sub: item.location_sub || extracted.location_sub || null,
    checkin_dates: ensureArray(item.checkin_dates?.length ? item.checkin_dates : extracted.checkin_dates),
    room_types: ensureArray(extracted.room_types),
    price_min_vnd: item.price_min_vnd ?? extracted.price_min_vnd ?? null,
    price_max_vnd: item.price_max_vnd ?? extracted.price_max_vnd ?? null,
    commission_vnd: item.commission_vnd ?? extracted.commission_vnd ?? null,
    includes_breakfast: item.includes_breakfast ?? extracted.includes_breakfast ?? null,
    extra_services: ensureArray(item.extra_services?.length ? item.extra_services : extracted.extra_services),
    contact_phone: item.contact_phone || extracted.contact_phone || null,
    contact_name: item.contact_name || extracted.contact_name || null,
    contact_company: item.contact_company || extracted.contact_company || item.sender_name || null,
    sender_id: item.sender_name || item.message_id || item.raw_message_id,
    sender_name: item.sender_name || "Unknown sender",
    msg_sent_at: item.sent_at || item.captured_at || item.created_at,
    matched: item.matched !== false,
    property_id: item.property_id || null,
    property_name: item.property_name || null,
    match_score: item.match_score ?? null,
    verification_method: item.verification_method || null,
    ai_verified: item.ai_verified ?? null,
    raw_message_status: item.raw_message_status || null,
    raw_text: item.raw_text || null,
    record_kind: "matched_hotel",
  };
}

function mapRejectedItem(item) {
  const extracted = item.extracted_payload && typeof item.extracted_payload === "object"
    ? item.extracted_payload
    : {};
  const rejectBucket = item.reject_bucket || inferRejectBucket(item.reason);

  return {
    hotel_id: item.id,
    raw_message_id: item.raw_message_id,
    hotel_name: extracted.hotel_name || extracted.name || `Rejected item ${item.source_msg_index ?? "-"}`,
    stars: extracted.stars ?? null,
    location: extracted.location || extracted.location_raw || "Unknown",
    location_sub: extracted.location_sub || null,
    checkin_dates: ensureArray(extracted.checkin_dates),
    room_types: ensureArray(extracted.room_types),
    price_min_vnd: extracted.price_min_vnd ?? null,
    price_max_vnd: extracted.price_max_vnd ?? null,
    commission_vnd: extracted.commission_vnd ?? null,
    includes_breakfast: extracted.includes_breakfast ?? null,
    extra_services: ensureArray(extracted.extra_services),
    contact_phone: extracted.contact_phone || null,
    contact_name: extracted.contact_name || item.sender_name || null,
    contact_company: extracted.contact_company || item.sender_name || null,
    sender_id: item.sender_name || item.message_id || item.raw_message_id,
    sender_name: item.sender_name || "Unknown sender",
    group_name: item.group_name || null,
    msg_sent_at: item.sent_at || item.captured_at || item.created_at,
    matched: false,
    property_id: null,
    property_name: null,
    match_score: null,
    reject_reason: item.reason || null,
    reject_bucket: rejectBucket,
    raw_text: item.raw_text || item.text_slice || null,
    raw_message_status: item.raw_message_status || null,
    source_msg_index: item.source_msg_index ?? null,
    record_kind: rejectBucket === "non_hotel" ? "non_hotel_reject" : "hotel_unmatched",
  };
}

export async function loadDashboardData(apiBaseUrl, signal) {
  const baseUrl = trimBaseUrl(apiBaseUrl);
  const [dealsData, nonHotelRejectedData, unmatchedHotelData, metricsData] = await Promise.all([
    fetchJson(`${baseUrl}/deals?limit=500`, signal),
    fetchJson(`${baseUrl}/deals/rejected?limit=500&bucket=non_hotel`, signal),
    fetchJson(`${baseUrl}/deals/rejected?limit=500&bucket=hotel_unmatched`, signal),
    fetchJson(`${baseUrl}/metrics/summary`, signal),
  ]);

  const acceptedRecords = ensureArray(dealsData.items).map(mapDealItem);
  const unmatchedHotelRecords = ensureArray(unmatchedHotelData.items).map(mapRejectedItem);
  const mergedHotelRecords = [...acceptedRecords, ...unmatchedHotelRecords].sort(
    (left, right) => getRecordTimestamp(right) - getRecordTimestamp(left),
  );

  return {
    acceptedRecords: mergedHotelRecords,
    rejectedRecords: ensureArray(nonHotelRejectedData.items).map(mapRejectedItem),
    metrics: metricsData,
  };
}

export async function loadRecordDetail(apiBaseUrl, record, signal) {
  if (!record || !record.raw_message_id) {
    return {
      record,
      deal: record,
      message: null,
    };
  }

  const baseUrl = trimBaseUrl(apiBaseUrl);
  const dealUrl = record.matched !== false && record.hotel_id && !String(record.hotel_id).startsWith("upload_")
    ? `${baseUrl}/deals/${record.hotel_id}`
    : null;

  const [dealDetail, messageDetail] = await Promise.all([
    dealUrl ? fetchJson(dealUrl, signal).catch(() => null) : Promise.resolve(null),
    fetchJson(`${baseUrl}/messages/${record.raw_message_id}`, signal),
  ]);

  const resolvedDeal = dealDetail?.item ? mapDealItem(dealDetail.item) : record;

  return {
    record,
    deal: {
      ...resolvedDeal,
      raw_text: dealDetail?.item?.raw_text || resolvedDeal.raw_text || messageDetail?.message?.text || record.raw_text || null,
    },
    message: messageDetail?.message || null,
  };
}
