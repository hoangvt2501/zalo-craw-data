"use strict";

function createPostgresRawMessageRepository(pool) {
  return {
    async healthCheck() {
      await pool.query("SELECT 1");
    },

    async insertRawMessage(rawMessage) {
      const sql = `
        INSERT INTO raw_messages (
          source,
          group_id,
          group_name,
          sender_id,
          sender_name,
          message_id,
          msg_type,
          text,
          text_hash,
          sent_at,
          raw_payload
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
        ON CONFLICT (source, message_id) DO NOTHING
        RETURNING id
      `;

      const values = [
        rawMessage.source,
        rawMessage.groupId,
        rawMessage.groupName,
        rawMessage.senderId,
        rawMessage.senderName,
        rawMessage.messageId,
        rawMessage.msgType,
        rawMessage.text,
        rawMessage.textHash,
        rawMessage.sentAt,
        rawMessage.rawPayload || {},
      ];

      const result = await pool.query(sql, values);
      if (result.rowCount > 0) {
        return { inserted: true, id: result.rows[0].id };
      }

      const existing = await pool.query(
        "SELECT id FROM raw_messages WHERE source = $1 AND message_id = $2 LIMIT 1",
        [rawMessage.source, rawMessage.messageId]
      );

      return {
        inserted: false,
        id: existing.rows[0]?.id || null,
      };
    },
  };
}

module.exports = { createPostgresRawMessageRepository };
