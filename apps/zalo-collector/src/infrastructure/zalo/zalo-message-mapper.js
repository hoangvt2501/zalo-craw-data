"use strict";

const crypto = require("crypto");

function normalizeText(value) {
  return typeof value === "string" ? value.replace(/\r\n/g, "\n").trim() : "";
}

function toDate(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  const date = new Date(n);
  return Number.isNaN(date.getTime()) ? null : date;
}

function hashText(senderId, text) {
  return crypto
    .createHash("sha256")
    .update(`${senderId || ""}|${text.replace(/\s+/g, " ").trim().slice(0, 600)}`)
    .digest("hex");
}

function createZaloMessageMapper() {
  return {
    toRawMessage(message) {
      const data = message?.data || {};
      const text = normalizeText(
        typeof data.content === "string"
          ? data.content
          : data.content?.content || data.content?.description || data.content?.title || ""
      );

      return {
        source: "zalo",
        groupId: message?.threadId || data.idTo || null,
        groupName: message?.threadName || data.threadName || null,
        senderId: data.uidFrom || null,
        senderName: data.dName || null,
        messageId: data.msgId || null,
        msgType: data.msgType || "chat.text",
        text,
        textHash: hashText(data.uidFrom, text),
        sentAt: toDate(data.ts),
        rawPayload: data,
      };
    },
  };
}

module.exports = { createZaloMessageMapper };
