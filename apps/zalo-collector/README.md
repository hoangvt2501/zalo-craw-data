# Zalo Collector

Node.js service.

Responsibility:

- Login/listen to Zalo groups.
- Normalize incoming messages.
- Insert raw messages into PostgreSQL.
- Keep processing very fast.

Not responsible for:

- LLM extraction.
- Property matching.
- Final deal writes.

Clean boundary:

```text
main.js
  -> application/captureZaloMessageUseCase.js
    -> ports/rawMessageRepository.js
  -> infrastructure/zalo/*
  -> infrastructure/postgres/*
```

## Local Commands

Run from this folder:

```powershell
cd C:\Users\Admin\Desktop\hotel-intel\hotel-intel-pipeline\apps\zalo-collector
$env:Path='C:\Program Files\nodejs;' + $env:Path
```

Install dependencies:

```powershell
npm.cmd install
```

Test PostgreSQL insert with a fake Zalo message:

```powershell
npm.cmd run smoke:insert-raw
```

List latest raw messages from PostgreSQL:

```powershell
npm.cmd run db:latest-raw
```

Start real Zalo collector:

```powershell
npm.cmd run dev
```

Expected behavior:

1. Terminal starts the Zalo QR login flow.
2. Scan the QR with the Zalo account used for group collection.
3. Keep the terminal running.
4. New group text messages are inserted into PostgreSQL table `raw_messages`.
5. Messages are inserted with `status = 'pending'`.

The collector intentionally does not call AI. AI processing belongs in `apps/ai-worker`.

## Database URL

The collector reads:

```text
hotel-intel-pipeline/.env
```

Required setting:

```env
DATABASE_URL=postgresql://hotel_intel_app:123456@localhost:5432/hotel_intel
```

If PostgreSQL password changes, update that value.
