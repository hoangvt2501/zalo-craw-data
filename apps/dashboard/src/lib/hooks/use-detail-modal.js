"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { loadRecordDetail } from "../api-client";

const EXIT_MS = 320;

export function useDetailModal(apiBaseUrl) {
  const [record, setRecord] = useState(null);
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const transitionKey = useRef(0);

  const openDetail = useCallback((rec) => {
    setRecord(rec);
    setPayload(null);
    setError("");
    setLoading(Boolean(rec.raw_message_id));
    setOpen(false);
    transitionKey.current += 1;
  }, []);

  const closeDetail = useCallback(() => {
    setOpen(false);
  }, []);

  // Fetch detail data when opened
  useEffect(() => {
    if (!open || !record || !record.raw_message_id) return undefined;

    const controller = new AbortController();
    setLoading(true);
    setError("");

    loadRecordDetail(apiBaseUrl, record, controller.signal)
      .then((data) => {
        setPayload(data);
        setLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(String(err.message || err));
        setLoading(false);
      });

    return () => controller.abort();
  }, [apiBaseUrl, open, record]);

  // Two-frame enter animation
  useEffect(() => {
    if (!record) return undefined;
    let f1 = 0;
    let f2 = 0;
    f1 = window.requestAnimationFrame(() => {
      f2 = window.requestAnimationFrame(() => setOpen(true));
    });
    return () => {
      window.cancelAnimationFrame(f1);
      window.cancelAnimationFrame(f2);
    };
  }, [record, transitionKey.current]);

  // Exit cleanup
  useEffect(() => {
    if (open || !record) return undefined;
    const id = window.setTimeout(() => {
      setRecord(null);
      setPayload(null);
      setError("");
      setLoading(false);
    }, EXIT_MS);
    return () => window.clearTimeout(id);
  }, [open, record]);

  return {
    record,
    payload,
    loading,
    error,
    open,
    openDetail,
    closeDetail,
  };
}
