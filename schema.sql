-- schema.sql: SQLite Initialization Script for Social Media Studio

-- Enable foreign key support in SQLite
PRAGMA foreign_keys = ON;

-- 1. Ingestion Source of Truth: Ingested Blog Posts / Markdown
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    source_type TEXT CHECK(source_type IN ('url', 'markdown')) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Platform Variants & Review Status Workflow
CREATE TABLE IF NOT EXISTS variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    platform TEXT CHECK(platform IN ('discord', 'telegram', 'x', 'linkedin')) NOT NULL,
    content TEXT NOT NULL,
    status TEXT CHECK(status IN ('draft', 'approved', 'rejected', 'published')) DEFAULT 'draft',
    validation_passed INTEGER DEFAULT 0 CHECK(validation_passed IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- 3. Durable Schedule Calendar & Idempotency Target
CREATE TABLE IF NOT EXISTS schedule_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    idempotency_key TEXT UNIQUE NOT NULL, -- Format: variant_{id}_slot_{id}
    status TEXT CHECK(status IN ('queued', 'processing', 'completed', 'failed')) DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
);

-- 4. Audit Trail & Real/Mock Adapter Publish History
CREATE TABLE IF NOT EXISTS publish_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER,
    variant_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    status TEXT CHECK(status IN ('success', 'failed', 'retried')) NOT NULL,
    response_payload TEXT, -- Stores JSON response or mock preview output
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slot_id) REFERENCES schedule_slots(id) ON DELETE SET NULL,
    FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_variants_post_id ON variants(post_id);
CREATE INDEX IF NOT EXISTS idx_schedule_slots_variant_id ON schedule_slots(variant_id);
CREATE INDEX IF NOT EXISTS idx_publish_history_variant_id ON publish_history(variant_id);