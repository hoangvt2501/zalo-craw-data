"use strict";

const fs = require("fs");
const path = require("path");

function loadDotEnv(filePath) {
  if (!fs.existsSync(filePath)) return;

  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;

    const [key, ...rest] = trimmed.split("=");
    if (!key || process.env[key]) continue;
    process.env[key] = rest.join("=").replace(/^["']|["']$/g, "");
  }
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env: ${name}`);
  return value;
}

function loadCollectorEnv() {
  const pipelineRoot = path.resolve(__dirname, "../../../..");
  loadDotEnv(path.join(pipelineRoot, ".env"));
  loadDotEnv(path.resolve(__dirname, "../..", ".env"));

  return {
    databaseUrl: requireEnv("DATABASE_URL"),
    sessionFile: process.env.ZALO_SESSION_FILE || "./var/zalo_session.json",
    instanceId: process.env.COLLECTOR_INSTANCE_ID || "local-zalo-collector-01",
  };
}

module.exports = { loadCollectorEnv, loadDotEnv };
