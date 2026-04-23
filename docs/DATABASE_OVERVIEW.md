# Database Overview

## Purpose

This document summarizes the PostgreSQL tables used by the hotel-intel pipeline.

It focuses on:

- core entity relationships
- pipeline data flow
- what each table is for

Schema source:

- `infra/postgres/migrations/001_initial.sql`

## Table Groups

### Intake And Queue

- `raw_messages`
  - the system-of-record for captured Zalo messages
  - also acts as the durable job queue for the AI worker

### Master Data

- `properties`
  - canonical hotel/property catalog used for matching

### Processing Output

- `hotel_deals`
  - accepted extracted hotel deals from one raw message
- `deal_rooms`
  - room-level detail rows for one accepted hotel deal
- `rejected_deals`
  - extracted rows that were rejected by rule or verifier

### Matching And AI Observability

- `match_attempts`
  - candidate-match attempts per extracted row
- `ai_call_logs`
  - provider/model/latency/error logs for LLM calls
- `processing_events`
  - stage-by-stage event log for one `raw_message`

### App And Audit

- `app_users`
  - dashboard users
- `audit_logs`
  - user action audit trail

## ER Diagram

```mermaid
erDiagram
    RAW_MESSAGES ||--o{ HOTEL_DEALS : produces
    RAW_MESSAGES ||--o{ REJECTED_DEALS : produces
    RAW_MESSAGES ||--o{ MATCH_ATTEMPTS : logs
    RAW_MESSAGES ||--o{ AI_CALL_LOGS : logs
    RAW_MESSAGES ||--o{ PROCESSING_EVENTS : emits

    PROPERTIES ||--o{ HOTEL_DEALS : matched_by
    PROPERTIES ||--o{ MATCH_ATTEMPTS : candidate

    HOTEL_DEALS ||--o{ DEAL_ROOMS : contains

    APP_USERS ||--o{ AUDIT_LOGS : writes

    RAW_MESSAGES {
        uuid id PK
        text source
        text group_id
        text group_name
        text sender_id
        text sender_name
        text message_id
        text msg_type
        text text
        text text_hash
        timestamptz sent_at
        timestamptz captured_at
        text status
        integer processing_attempts
        timestamptz processed_at
        text last_error
        jsonb raw_payload
    }

    PROPERTIES {
        text id PK
        text name
        text address
        text district
        text province
        integer stars
        text[] aliases
        jsonb metadata
    }

    HOTEL_DEALS {
        uuid id PK
        uuid raw_message_id FK
        integer source_msg_index
        text property_id FK
        text property_name
        text hotel_name
        integer stars
        text location
        text location_sub
        bigint price_min_vnd
        bigint price_max_vnd
        bigint commission_vnd
        numeric match_score
        boolean matched
        text verification_method
        boolean ai_verified
        jsonb extracted_payload
    }

    DEAL_ROOMS {
        uuid id PK
        uuid hotel_deal_id FK
        text name
        integer quantity
        bigint price_vnd
        text price_per
        boolean includes_breakfast
        jsonb raw_payload
    }

    REJECTED_DEALS {
        uuid id PK
        uuid raw_message_id FK
        integer source_msg_index
        text reason
        text text_slice
        jsonb extracted_payload
        jsonb candidate_property
        jsonb verifier_payload
    }

    MATCH_ATTEMPTS {
        uuid id PK
        uuid raw_message_id FK
        integer source_msg_index
        text extracted_hotel_name
        text extracted_location
        text candidate_property_id FK
        numeric rule_score
        boolean verifier_called
        boolean verifier_verified
        text verifier_reason
        text verifier_error
    }

    AI_CALL_LOGS {
        uuid id PK
        uuid raw_message_id FK
        text purpose
        text provider
        text model
        text status
        integer http_status
        integer latency_ms
        integer retry_count
        text error
    }

    PROCESSING_EVENTS {
        uuid id PK
        uuid raw_message_id FK
        text event_type
        text message
        jsonb payload
        timestamptz created_at
    }

    APP_USERS {
        uuid id PK
        text email
        text display_name
        text role
        boolean active
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        text action
        text entity_type
        text entity_id
        jsonb payload
        timestamptz created_at
    }
```

## Pipeline Flow

```mermaid
flowchart LR
    A["Zalo Collector"] --> B["raw_messages"]
    B --> C["AI Worker"]
    C --> D["Extractor"]
    D --> E["Rule Match vs properties"]
    E --> F{"confidence"}
    F -->|"high"| G["hotel_deals"]
    F -->|"medium"| H["LLM verifier"]
    F -->|"low / no match"| I["rejected_deals"]
    H -->|"verified"| G
    H -->|"rejected / failed"| I
    G --> J["deal_rooms"]
    C --> K["processing_events"]
    C --> L["match_attempts"]
    C --> M["ai_call_logs"]
    N["API"] --> B
    N --> G
    N --> I
    N --> K
    O["Dashboard"] --> N
```

## Review-Oriented View

```mermaid
flowchart TD
    RM["raw_messages
    one message from Zalo"] --> HD["hotel_deals
    accepted extracted rows"]
    RM --> RD["rejected_deals
    rejected extracted rows"]
    RM --> PE["processing_events
    timeline and stage logs"]
    HD --> DR["deal_rooms
    room detail"]
    HD --> P["properties
    canonical property"]
    RD --> CP["candidate_property JSON
    optional best guess"]
```

## Practical Reading Guide

### If You Want To Know What Came In

- start at `raw_messages`

### If You Want Accepted Hotel Rows

- read `hotel_deals`
- then join `deal_rooms`
- optionally join `properties`

### If You Want Rejected Rows

- read `rejected_deals`

### If You Want Why Something Happened

- read `processing_events`
- then `match_attempts`
- then `ai_call_logs`

### If You Want User Review Audit

- read `audit_logs`
- join `app_users`

## Important Cardinality Notes

- one `raw_message` can create many `hotel_deals`
- one `raw_message` can create many `rejected_deals`
- one `hotel_deal` can create many `deal_rooms`
- one `property` can be linked by many `hotel_deals`
- one `raw_message` can have many `processing_events`

## Key Constraints

- `raw_messages`
  - unique: `(source, message_id)`
- `hotel_deals`
  - unique: `(raw_message_id, source_msg_index)`
- `deal_rooms`
  - cascade delete when parent `hotel_deal` is deleted

## Recommended Mental Model

Think about the schema in three layers:

1. `raw_messages` is the intake and queue layer
2. `hotel_deals` and `rejected_deals` are the decision/output layer
3. `processing_events`, `match_attempts`, and `ai_call_logs` are the observability layer
