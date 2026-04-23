"use strict";

const { Zalo, ThreadType } = require("zca-js");

const IGNORED_MSG_TYPES = new Set([
  "chat.sticker",
  "chat.gif",
  "chat.photo",
  "chat.video",
  "chat.voice",
  "chat.recommended",
  "chat.location",
  "chat.location.new",
  "chat.video.msg",
]);

function extractText(content) {
  if (typeof content === "string") return content.trim();
  if (content && typeof content === "object") {
    return String(content.content || content.description || content.title || content.text || "").trim();
  }
  return "";
}

function shouldCaptureMessage(message) {
  if (!message || message.type !== ThreadType.Group || message.isSelf) return false;

  const data = message.data || {};
  if (IGNORED_MSG_TYPES.has(data.msgType)) return false;

  return extractText(data.content).length > 20;
}

async function createZaloClient() {
  const zalo = new Zalo({ selfListen: false, checkUpdate: true, logging: false });
  const api = await zalo.loginQR();

  return {
    onMessage(handler) {
      api.listener.on("message", handler);
    },

    start() {
      api.listener.start();
    },
  };
}

module.exports = { createZaloClient, shouldCaptureMessage };
