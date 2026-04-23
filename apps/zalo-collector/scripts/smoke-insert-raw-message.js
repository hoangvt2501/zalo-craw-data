"use strict";

const { Pool } = require("pg");

const { loadCollectorEnv } = require("../src/config/env");
const { captureZaloMessageUseCase } = require("../src/application/capture-zalo-message");
const { createPostgresRawMessageRepository } = require("../src/infrastructure/postgres/postgres-raw-message-repository");
const { createZaloMessageMapper } = require("../src/infrastructure/zalo/zalo-message-mapper");

function maskDatabaseUrl(url) {
  return String(url).replace(/:\/\/([^:]+):([^@]+)@/, "://$1:***@");
}

function buildFakeZaloMessage() {
  const now = Date.now();
  return {
    threadId: "group_test_001",
    threadName: "Nhom test Zalo",
    isSelf: false,
    data: {
      idTo: "group_test_001",
      threadName: "Nhom test Zalo",
      uidFrom: "sender_001",
      dName: "Anh Nam",
      msgId: `smoke_${now}`,
      msgType: "chat.text",
      ts: now,
      content: `Vinpearl Resort Ha Long:
- 30/4: Deluxe Ocean 3000k/dem an sang
- 01/5: Deluxe Ocean 3500k/dem an sang
lien he 0909123456`,
    },
  };
}

async function main() {
  const env = loadCollectorEnv();
  console.log("[SMOKE] database:", maskDatabaseUrl(env.databaseUrl));

  const pool = new Pool({ connectionString: env.databaseUrl });
  const rawMessageRepository = createPostgresRawMessageRepository(pool);
  const messageMapper = createZaloMessageMapper();

  try {
    await rawMessageRepository.healthCheck();

    const result = await captureZaloMessageUseCase(buildFakeZaloMessage(), {
      rawMessageRepository,
      messageMapper,
    });

    const latest = await pool.query(`
      SELECT id, source, group_name, sender_name, status, text
      FROM raw_messages
      ORDER BY captured_at DESC
      LIMIT 1
    `);

    console.log("[SMOKE] insert result:", result);
    console.log("[SMOKE] latest raw message:", latest.rows[0]);
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error("[SMOKE ERR]", err.message);
  if (err.message.includes("password authentication failed")) {
    console.error("");
    console.error("PostgreSQL login failed. In pgAdmin, run this on database hotel_intel:");
    console.error("ALTER USER hotel_intel_app WITH PASSWORD 'change_me';");
    console.error("GRANT ALL PRIVILEGES ON DATABASE hotel_intel TO hotel_intel_app;");
    console.error("GRANT ALL ON SCHEMA public TO hotel_intel_app;");
    console.error("");
    console.error("Or update hotel-intel-pipeline/.env DATABASE_URL to match your real username/password.");
  }
  process.exit(1);
});
