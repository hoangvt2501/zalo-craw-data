function resolveLocale(language = "vi") {
  return language === "en" ? "en-US" : "vi-VN";
}

export function formatCurrency(value, language = "vi") {
  if (!value) {
    return "-";
  }
  return `${new Intl.NumberFormat(resolveLocale(language)).format(Number(value))} VND`;
}

export function formatCompact(value, language = "vi") {
  if (!value) {
    return "-";
  }
  const numeric = Number(value);
  if (numeric >= 1_000_000) {
    const suffix = language === "en" ? "m" : "tr";
    return `${Number((numeric / 1_000_000).toFixed(1)).toLocaleString(resolveLocale(language))}${suffix}`;
  }
  if (numeric >= 1_000) {
    return `${Math.round(numeric / 1_000).toLocaleString(resolveLocale(language))}k`;
  }
  return new Intl.NumberFormat(resolveLocale(language)).format(numeric);
}

export function formatDateTime(value, language = "vi") {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString(resolveLocale(language));
}

export function formatDate(value, language = "vi") {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleDateString(resolveLocale(language));
}

export function getLocale(language = "vi") {
  return resolveLocale(language);
}

export function getTimestamp(record) {
  if (record.ts_ms) {
    return Number(record.ts_ms);
  }
  if (record.msg_sent_at) {
    return new Date(record.msg_sent_at).getTime();
  }
  return 0;
}

export function getMinPrice(record) {
  if (record.price_min_vnd) {
    return Number(record.price_min_vnd);
  }
  const roomPrices = (record.room_types || [])
    .map((room) => Number(room.price_vnd))
    .filter((value) => value > 0);
  return roomPrices.length ? Math.min(...roomPrices) : null;
}

export function getMaxPrice(record) {
  if (record.price_max_vnd) {
    return Number(record.price_max_vnd);
  }
  const roomPrices = (record.room_types || [])
    .map((room) => Number(room.price_vnd))
    .filter((value) => value > 0);
  return roomPrices.length ? Math.max(...roomPrices) : null;
}

export function getContact(record) {
  return [record.contact_name, record.contact_phone].filter(Boolean).join(" - ") || "-";
}

export function getGroupKey(record) {
  if (record.matched && record.property_id) {
    return `property:${record.property_id}`;
  }
  return `raw:${String(record.hotel_name || "unknown")
    .toLowerCase()
    .replace(/\s+/g, "-")}`;
}

export function buildGroups(records) {
  const groups = new Map();
  for (const record of records) {
    const key = getGroupKey(record);
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key).push(record);
  }
  for (const offers of groups.values()) {
    offers.sort((left, right) => (getMinPrice(left) || Number.MAX_SAFE_INTEGER) - (getMinPrice(right) || Number.MAX_SAFE_INTEGER));
  }
  return groups;
}

export function sortGroupEntries(entries, sortKey) {
  return [...entries].sort((leftEntry, rightEntry) => {
    const left = leftEntry[1];
    const right = rightEntry[1];
    const leftLead = left[0];
    const rightLead = right[0];

    if (sortKey === "offers_d") {
      return right.length - left.length;
    }
    if (sortKey === "date_d") {
      return Math.max(...right.map(getTimestamp)) - Math.max(...left.map(getTimestamp));
    }
    if (sortKey === "com_d") {
      return Math.max(...right.map((offer) => Number(offer.commission_vnd) || 0)) -
        Math.max(...left.map((offer) => Number(offer.commission_vnd) || 0));
    }
    if (sortKey === "stars_d") {
      return (Number(rightLead.stars) || 0) - (Number(leftLead.stars) || 0);
    }
    return (getMinPrice(leftLead) || Number.MAX_SAFE_INTEGER) - (getMinPrice(rightLead) || Number.MAX_SAFE_INTEGER);
  });
}

export function sortFlatRecords(records, sortState) {
  const next = [...records];
  next.sort((left, right) => {
    const direction = sortState?.dir || 1;
    const column = sortState?.column || "price";

    if (column === "price") {
      return direction * ((getMinPrice(left) || Number.MAX_SAFE_INTEGER) - (getMinPrice(right) || Number.MAX_SAFE_INTEGER));
    }
    if (column === "commission_vnd") {
      return direction * ((Number(left.commission_vnd) || 0) - (Number(right.commission_vnd) || 0));
    }
    if (column === "sender_name") {
      return direction * String(left.sender_name || "").localeCompare(String(right.sender_name || ""), "vi");
    }
    return direction * String(left.hotel_name || "").localeCompare(String(right.hotel_name || ""), "vi");
  });
  return next;
}

export function getLocationOptions(records) {
  return [...new Set(records.map((record) => record.location).filter(Boolean))].sort((left, right) =>
    left.localeCompare(right, "vi"),
  );
}

export function filterRecords(records, filters) {
  return records.filter((record) => {
    if (filters.query) {
      const haystack = [
        record.hotel_name,
        record.location,
        record.location_sub,
        record.property_name,
        record.contact_name,
        record.contact_phone,
        record.contact_company,
        record.sender_name,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(filters.query.toLowerCase())) {
        return false;
      }
    }

    if (filters.location && record.location !== filters.location) {
      return false;
    }

    if (filters.stars !== "") {
      if (filters.stars === "0") {
        if (record.stars) {
          return false;
        }
      } else if (Number(record.stars) !== Number(filters.stars)) {
        return false;
      }
    }

    if (filters.price) {
      const [minimum, maximum] = filters.price.split("-").map(Number);
      const price = getMinPrice(record);
      if (!price || price < minimum || price >= maximum) {
        return false;
      }
    }

    return true;
  });
}

export function computeKpis(records) {
  const groups = buildGroups(records);
  const prices = records.map(getMinPrice).filter(Boolean);
  const commissions = records.map((record) => Number(record.commission_vnd)).filter((value) => value > 0);
  const senders = [...new Set(records.map((record) => record.sender_id || record.sender_name).filter(Boolean))];
  const companies = [...new Set(records.map((record) => record.contact_company).filter(Boolean))];

  return {
    uniqueHotels: groups.size,
    offers: records.length,
    bestPrice: prices.length ? Math.min(...prices) : null,
    avgCommission: commissions.length ? Math.round(commissions.reduce((sum, value) => sum + value, 0) / commissions.length) : null,
    senders: senders.length,
    matched: records.filter((record) => record.matched).length,
    commissionOffers: commissions.length,
    companies: companies.length,
    lastUpdated: records.length ? Math.max(...records.map(getTimestamp)) : null,
  };
}

export function getLocationInsights(records, language = "vi") {
  const map = new Map();
  for (const record of records) {
    const key = record.location || "Khac";
    if (!map.has(key)) {
      map.set(key, { prices: [], commissions: [], offers: 0, matched: 0 });
    }
    const entry = map.get(key);
    entry.offers += 1;
    entry.matched += record.matched ? 1 : 0;
    const price = getMinPrice(record);
    if (price) {
      entry.prices.push(price);
    }
    if (record.commission_vnd) {
      entry.commissions.push(Number(record.commission_vnd));
    }
  }

  return [...map.entries()]
    .map(([name, stats]) => ({
      id: name,
      title: name,
      subtitle: language === "en" ? `${stats.offers} offers` : `${stats.offers} offer`,
      count: stats.offers,
      share: records.length ? Math.round((stats.offers / records.length) * 100) : 0,
      avgPrice: stats.prices.length
        ? Math.round(stats.prices.reduce((sum, value) => sum + value, 0) / stats.prices.length)
        : null,
      maxCommission: stats.commissions.length ? Math.max(...stats.commissions) : null,
      matched: stats.matched,
    }))
    .sort((left, right) => right.count - left.count);
}

export function getSenderInsights(records, language = "vi") {
  const map = new Map();
  for (const record of records) {
    const key = record.sender_name || record.contact_name || "Unknown";
    if (!map.has(key)) {
      map.set(key, {
        prices: [],
        commissions: [],
        offers: 0,
        matched: 0,
        company: record.contact_company || "-",
      });
    }
    const entry = map.get(key);
    entry.offers += 1;
    entry.matched += record.matched ? 1 : 0;
    const price = getMinPrice(record);
    if (price) {
      entry.prices.push(price);
    }
    if (record.commission_vnd) {
      entry.commissions.push(Number(record.commission_vnd));
    }
  }

  return [...map.entries()]
    .map(([name, stats]) => ({
      id: name,
      title: name,
      subtitle: stats.company,
      count: stats.offers,
      share: records.length ? Math.round((stats.offers / records.length) * 100) : 0,
      avgPrice: stats.prices.length
        ? Math.round(stats.prices.reduce((sum, value) => sum + value, 0) / stats.prices.length)
        : null,
      maxCommission: stats.commissions.length ? Math.max(...stats.commissions) : null,
      matched: stats.matched,
    }))
    .sort((left, right) => right.count - left.count);
}

export function parseDealUpload(text) {
  const trimmed = text.trim();
  if (!trimmed) {
    return [];
  }

  try {
    const parsedJson = JSON.parse(trimmed);
    if (Array.isArray(parsedJson)) {
      return parsedJson.map(normalizeRecord).filter(Boolean);
    }
    if (parsedJson && typeof parsedJson === "object") {
      return [normalizeRecord(parsedJson, 0)].filter(Boolean);
    }
  } catch {
    // Fall through to JSONL parsing.
  }

  return trimmed
    .split(/\r?\n/)
    .map((line, index) => {
      try {
        return normalizeRecord(JSON.parse(line), index);
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

function normalizeRecord(record, index = 0) {
  if (!record || typeof record !== "object") {
    return null;
  }

  return {
    hotel_id: record.hotel_id || record.id || `upload_${index}`,
    hotel_name: record.hotel_name || record.property_name || record.name || `Record ${index + 1}`,
    stars: record.stars ?? null,
    location: record.location || record.matched_property_province || record.province || "Unknown",
    location_sub: record.location_sub || record.matched_property_district || null,
    checkin_dates: Array.isArray(record.checkin_dates)
      ? record.checkin_dates
      : typeof record.checkin_dates === "string" && record.checkin_dates
        ? [record.checkin_dates]
        : [],
    room_types: Array.isArray(record.room_types) ? record.room_types : [],
    price_min_vnd: record.price_min_vnd ? Number(record.price_min_vnd) : null,
    price_max_vnd: record.price_max_vnd ? Number(record.price_max_vnd) : null,
    commission_vnd: record.commission_vnd ? Number(record.commission_vnd) : null,
    includes_breakfast: record.includes_breakfast ?? null,
    extra_services: Array.isArray(record.extra_services) ? record.extra_services : [],
    contact_phone: record.contact_phone || null,
    contact_name: record.contact_name || record.sender_name || null,
    contact_company: record.contact_company || record.sender_name || null,
    sender_id: record.sender_id || record.sender_name || `upload_sender_${index}`,
    sender_name: record.sender_name || record.contact_name || "Uploaded source",
    msg_sent_at: record.msg_sent_at || record.logged_at || new Date().toISOString(),
    matched: record.matched ?? (record.decision === "accepted" ? true : Boolean(record.property_id || record.matched_property_id)),
    property_id: record.property_id || record.matched_property_id || null,
    property_name: record.property_name || record.matched_property_name || null,
    match_score: record.match_score ?? record.best_candidate_score ?? null,
    reject_reason: record.reject_reason || record.reason || null,
    raw_text: record.raw_text || record.text || null,
  };
}
