"use strict";

const { Pool } = require("pg");

const { loadCollectorEnv } = require("./config/env");
const { captureZaloMessageUseCase } = require("./application/capture-zalo-message");
const { createPostgresRawMessageRepository } = require("./infrastructure/postgres/postgres-raw-message-repository");
const { createZaloClient, shouldCaptureMessage } = require("./infrastructure/zalo/zalo-client");
const { createZaloMessageMapper } = require("./infrastructure/zalo/zalo-message-mapper");

async function main() {
  const env = loadCollectorEnv();
  const pool = new Pool({ connectionString: env.databaseUrl });
  const rawMessageRepository = createPostgresRawMessageRepository(pool);
  const messageMapper = createZaloMessageMapper();

  await rawMessageRepository.healthCheck();

  const deps = { rawMessageRepository, messageMapper };
  const metrics = { incoming: 0, ignored: 0, captured: 0, duplicate: 0, failed: 0 };

  console.log("=".repeat(60));
  console.log("Hotel Intel - Zalo Collector");
  console.log("=".repeat(60));
  console.log(`Instance : ${env.instanceId}`);
  console.log("Storage  : PostgreSQL raw_messages");
  console.log("-".repeat(60));

  const client = await createZaloClient(env);

  client.onMessage(async message => {
    metrics.incoming++;

    try {
      if (!shouldCaptureMessage(message)) {
        metrics.ignored++;
        return;
      }

      const result = await captureZaloMessageUseCase(message, deps);
      metrics[result.status] = (metrics[result.status] || 0) + 1;

      const data = message.data || {};
      console.log(
        `[RAW:${result.status}] group=${message.threadId || data.idTo || "?"} ` +
        `msg=${data.msgId || "?"} id=${result.id || "-"}`
      );
    } catch (err) {
      metrics.failed++;
      console.error("[CAPTURE ERR]", err.message);
    }
  });

  setInterval(() => {
    console.log(
      `[METRICS collector] incoming=${metrics.incoming} ignored=${metrics.ignored} ` +
      `captured=${metrics.captured} duplicate=${metrics.duplicate} failed=${metrics.failed}`
    );
  }, 60_000).unref();

  process.on("SIGINT", async () => {
    console.log("\n[SHUTDOWN] closing PostgreSQL pool...");
    await pool.end();
    process.exit(0);
  });

  client.start();
  console.log("Listener is running. Press Ctrl+C to stop.");
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
