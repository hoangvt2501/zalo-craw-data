"use strict";

const { Pool } = require("pg");

const { loadCollectorEnv } = require("../src/config/env");

function maskDatabaseUrl(url) {
  return String(url).replace(/:\/\/([^:]+):([^@]+)@/, "://$1:***@");
}

async function main() {
  const env = loadCollectorEnv();
  console.log("[DB] database:", maskDatabaseUrl(env.databaseUrl));

  const pool = new Pool({ connectionString: env.databaseUrl });

  try {
    const result = await pool.query(`
      SELECT
        id,
        source,
        group_name,
        sender_name,
        message_id,
        status,
        captured_at,
        left(replace(text, E'\\n', ' '), 140) AS preview
      FROM raw_messages
      ORDER BY captured_at DESC
      LIMIT 10
    `);

    if (result.rows.length === 0) {
      console.log("[DB] no raw messages found");
      return;
    }

    console.table(result.rows);
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error("[DB ERR]", err.message);
  process.exit(1);
});

