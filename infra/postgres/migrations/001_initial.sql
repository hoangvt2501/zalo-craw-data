CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS raw_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL DEFAULT 'zalo',
  group_id TEXT,
  group_name TEXT,
  sender_id TEXT,
  sender_name TEXT,
  message_id TEXT,
  msg_type TEXT,
  text TEXT NOT NULL,
  text_hash TEXT NOT NULL,
  sent_at TIMESTAMPTZ,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  status TEXT NOT NULL DEFAULT 'pending',
  processing_attempts INTEGER NOT NULL DEFAULT 0,
  locked_by TEXT,
  locked_at TIMESTAMPTZ,
  processed_at TIMESTAMPTZ,
  last_error TEXT,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (source, message_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_messages_status_captured
  ON raw_messages (status, captured_at);

CREATE INDEX IF NOT EXISTS idx_raw_messages_text_hash
  ON raw_messages (text_hash);

CREATE TABLE IF NOT EXISTS properties (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  address TEXT,
  district TEXT,
  province TEXT,
  stars INTEGER,
  aliases TEXT[] NOT NULL DEFAULT '{}',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_properties_province
  ON properties (province);

CREATE TABLE IF NOT EXISTS hotel_deals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_message_id UUID NOT NULL REFERENCES raw_messages(id),
  source_msg_index INTEGER NOT NULL DEFAULT 0,
  property_id TEXT REFERENCES properties(id),
  property_name TEXT,
  hotel_name TEXT NOT NULL,
  stars INTEGER,
  location TEXT,
  location_sub TEXT,
  location_raw TEXT,
  address TEXT,
  checkin_dates JSONB NOT NULL DEFAULT '[]'::jsonb,
  checkout_date TEXT,
  duration_nights INTEGER,
  price_min_vnd BIGINT,
  price_max_vnd BIGINT,
  commission_vnd BIGINT,
  commission_pct NUMERIC(8, 4),
  commission_type TEXT,
  includes_breakfast BOOLEAN,
  extra_services JSONB NOT NULL DEFAULT '[]'::jsonb,
  contact_phone TEXT,
  contact_name TEXT,
  contact_company TEXT,
  match_score NUMERIC(5, 4),
  matched BOOLEAN NOT NULL DEFAULT false,
  property_verified BOOLEAN,
  verification_method TEXT,
  ai_verified BOOLEAN,
  ai_verification_reason TEXT,
  extracted_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (raw_message_id, source_msg_index)
);

CREATE INDEX IF NOT EXISTS idx_hotel_deals_property
  ON hotel_deals (property_id);

CREATE INDEX IF NOT EXISTS idx_hotel_deals_created
  ON hotel_deals (created_at DESC);

CREATE TABLE IF NOT EXISTS deal_rooms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hotel_deal_id UUID NOT NULL REFERENCES hotel_deals(id) ON DELETE CASCADE,
  name TEXT,
  quantity INTEGER,
  price_vnd BIGINT,
  price_per TEXT,
  label TEXT,
  includes_breakfast BOOLEAN,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS match_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_message_id UUID NOT NULL REFERENCES raw_messages(id),
  source_msg_index INTEGER NOT NULL DEFAULT 0,
  extracted_hotel_name TEXT,
  extracted_location TEXT,
  candidate_property_id TEXT REFERENCES properties(id),
  candidate_property_name TEXT,
  rule_score NUMERIC(5, 4),
  verifier_called BOOLEAN NOT NULL DEFAULT false,
  verifier_verified BOOLEAN,
  verifier_reason TEXT,
  verifier_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rejected_deals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_message_id UUID REFERENCES raw_messages(id),
  source_msg_index INTEGER,
  reason TEXT NOT NULL,
  text_slice TEXT,
  extracted_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  candidate_property JSONB,
  verifier_payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_call_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_message_id UUID REFERENCES raw_messages(id),
  purpose TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  status TEXT NOT NULL,
  http_status INTEGER,
  latency_ms INTEGER,
  retry_count INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS processing_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_message_id UUID REFERENCES raw_messages(id),
  event_type TEXT NOT NULL,
  message TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  display_name TEXT,
  password_hash TEXT,
  role TEXT NOT NULL DEFAULT 'viewer',
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES app_users(id),
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

