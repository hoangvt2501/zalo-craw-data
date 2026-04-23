"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { loadDashboardData } from "../api-client";
import {
  buildGroups,
  computeKpis,
  filterRecords,
  getLocationInsights,
  getLocationOptions,
  getSenderInsights,
  sortFlatRecords,
  sortGroupEntries,
  parseDealUpload,
} from "../dashboard-utils";

const INITIAL_FILTERS = {
  query: "",
  location: "",
  stars: "",
  price: "",
  sort: "price_a",
};

const POLL_INTERVAL_MS = 15_000;

const NON_HOTEL_REJECT_REASONS = new Set([
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

function isNonHotelRejected(record) {
  if (!record || record.matched !== false) {
    return false;
  }

  if (record.reject_bucket === "non_hotel" || record.record_kind === "non_hotel_reject") {
    return true;
  }

  const reason = String(record.reject_reason || record.reason || "").trim();
  return NON_HOTEL_REJECT_REASONS.has(reason);
}

function splitUploaded(records) {
  return {
    accepted: records.filter((record) => record.matched !== false || !isNonHotelRejected(record)),
    rejected: records.filter((record) => isNonHotelRejected(record)),
  };
}

function dataReducer(state, action) {
  switch (action.type) {
    case "LOAD_START":
      return { ...state, loading: true };
    case "LOAD_SUCCESS":
      return {
        ...state,
        accepted: action.accepted,
        rejected: action.rejected,
        metrics: action.metrics,
        fileStatus: action.fileStatus,
        loadError: "",
        loading: false,
      };
    case "LOAD_ERROR":
      return {
        ...state,
        accepted: [],
        rejected: [],
        metrics: null,
        fileStatus: action.fileStatus,
        loadError: action.error,
        loading: false,
      };
    case "UPLOAD":
      return {
        ...state,
        accepted: action.accepted,
        rejected: action.rejected,
        metrics: null,
        fileStatus: action.fileStatus,
        loadError: "",
        loading: false,
      };
    default:
      return state;
  }
}

export function useDashboardState(apiBaseUrl) {
  const isEnglish = useIsEnglish();

  const [data, dispatch] = useReducer(dataReducer, {
    accepted: [],
    rejected: [],
    metrics: null,
    fileStatus: isEnglish ? "loading API..." : "đang tải API...",
    loadError: "",
    loading: true,
  });

  const [theme, setTheme] = useState("night");
  const [language, setLanguage] = useState("vi");
  const [activePage, setActivePage] = useState("deals");
  const [view, setView] = useState("group");
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [flatSort, setFlatSort] = useState({ column: "price", dir: 1 });
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [compareKeys, setCompareKeys] = useState([]);
  const [toastMessage, setToastMessage] = useState("");

  // Load persisted preferences
  useEffect(() => {
    const savedTheme = window.localStorage.getItem("hotel-intel-theme");
    const savedLang = window.localStorage.getItem("hotel-intel-language");
    if (savedTheme === "paper" || savedTheme === "night") setTheme(savedTheme);
    if (savedLang === "en" || savedLang === "vi") setLanguage(savedLang);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.body.dataset.theme = theme;
    window.localStorage.setItem("hotel-intel-theme", theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.lang = language;
    window.localStorage.setItem("hotel-intel-language", language);
  }, [language]);

  // Toast auto-dismiss
  useEffect(() => {
    if (!toastMessage) return undefined;
    const id = window.setTimeout(() => setToastMessage(""), 2200);
    return () => window.clearTimeout(id);
  }, [toastMessage]);

  // Auto-reload with visibility gating
  const isVisible = useRef(true);
  useEffect(() => {
    function onVisibilityChange() {
      isVisible.current = !document.hidden;
    }
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, []);

  const fetchData = useCallback(
    (signal) => {
      const eng = language === "en";
      dispatch({ type: "LOAD_START" });

      loadDashboardData(apiBaseUrl, signal)
        .then((result) => {
          const summary = result.metrics?.summary || null;
          const statusText = summary
            ? `API live - ${result.acceptedRecords.length} hotel rows (${summary.hotel_deals} matched DB) / ${result.rejectedRecords.length} non-hotel`
            : `API live - ${result.acceptedRecords.length} hotel rows / ${result.rejectedRecords.length} non-hotel`;

          dispatch({
            type: "LOAD_SUCCESS",
            accepted: result.acceptedRecords,
            rejected: result.rejectedRecords,
            metrics: summary,
            fileStatus: statusText,
          });
        })
        .catch((err) => {
          if (signal?.aborted) return;
          dispatch({
            type: "LOAD_ERROR",
            fileStatus: eng ? "API error" : "lỗi API",
            error: String(err.message || err),
          });
          setToastMessage(eng ? "Cannot load API" : "Không load được API");
        });
    },
    [apiBaseUrl, language],
  );

  useEffect(() => {
    const controller = new AbortController();
    fetchData(controller.signal);

    const id = window.setInterval(() => {
      if (isVisible.current) {
        fetchData(null);
      }
    }, POLL_INTERVAL_MS);

    return () => {
      controller.abort();
      window.clearInterval(id);
    };
  }, [fetchData]);

  // Computed data
  const filteredRecords = filterRecords(data.accepted, filters);
  const allGroups = buildGroups(data.accepted);
  const groupedEntries = sortGroupEntries(
    Array.from(buildGroups(filteredRecords).entries()),
    filters.sort,
  );
  const flatRecords = sortFlatRecords(filteredRecords, flatSort);
  const kpis = computeKpis(filteredRecords);
  const locationInsights = getLocationInsights(data.accepted, language);
  const senderInsights = getSenderInsights(data.accepted, language);
  const locationOptions = getLocationOptions(data.accepted);
  const compareGroups = compareKeys
    .map((key) => {
      const offers = allGroups.get(key);
      return offers ? { key, offers } : null;
    })
    .filter(Boolean);

  // Actions
  function handleFileSelected(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    file.text().then((text) => {
      const parsed = parseDealUpload(text);
      if (!parsed.length) {
        setToastMessage(language === "en" ? "Invalid file" : "File không hợp lệ");
        return;
      }

      const { accepted, rejected } = splitUploaded(parsed);
      dispatch({
        type: "UPLOAD",
        accepted,
        rejected,
        fileStatus: `upload ${file.name} - ${accepted.length} hotel rows / ${rejected.length} non-hotel`,
      });

      setFilters(INITIAL_FILTERS);
      setCompareKeys([]);
      setExpandedKeys([]);
      setActivePage("deals");
      setToastMessage(
        language === "en" ? `Loaded ${parsed.length} records` : `Đã nạp ${parsed.length} bản ghi`,
      );
    });
  }

  function handleFilterChange(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  function handleClearFilters() {
    setFilters(INITIAL_FILTERS);
  }

  function toggleExpanded(key) {
    setExpandedKeys((current) =>
      current.includes(key) ? current.filter((item) => item !== key) : [...current, key],
    );
  }

  function toggleCompare(key) {
    setCompareKeys((current) => {
      if (current.includes(key)) return current.filter((item) => item !== key);
      if (current.length >= 3) {
        setToastMessage(
          language === "en" ? "Compare up to 3 groups" : "Chỉ so sánh tối đa 3 nhóm",
        );
        return current;
      }
      return [...current, key];
    });
  }

  function changeFlatSort(column, dir) {
    setFlatSort({ column, dir });
  }

  function handleReload() {
    fetchData(null);
  }

  function handleSelectLocation(location) {
    setFilters((current) => ({ ...current, location, query: "" }));
    setActivePage("deals");
  }

  return {
    // Data
    acceptedRecords: data.accepted,
    rejectedRecords: data.rejected,
    metricsSummary: data.metrics,
    fileStatus: data.fileStatus,
    loadError: data.loadError,
    filteredRecords,
    groupedEntries,
    flatRecords,
    kpis,
    locationInsights,
    senderInsights,
    locationOptions,
    compareGroups,

    // UI state
    theme,
    language,
    activePage,
    view,
    filters,
    flatSort,
    expandedKeys,
    compareKeys,
    toastMessage,

    // Actions
    setTheme,
    setLanguage,
    setActivePage,
    setView,
    handleFileSelected,
    handleFilterChange,
    handleClearFilters,
    toggleExpanded,
    toggleCompare,
    changeFlatSort,
    handleReload,
    handleSelectLocation,
    setCompareKeys,
  };
}

export function useIsEnglish() {
  // Stub for SSR - actual language is in state
  return false;
}
