-- ==============================================================================
-- Daily Dhikr - PostgreSQL & Supabase Database Schema
-- ==============================================================================

-- 1. Source Records Table
CREATE TABLE IF NOT EXISTS source_records (
    id VARCHAR(36) PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    reference VARCHAR(255) NOT NULL,
    hadith_grade VARCHAR(100),
    grading_source VARCHAR(255),
    verification_notes TEXT,
    verified_by VARCHAR(100),
    verified_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'UNVERIFIED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_records_type ON source_records(source_type);
CREATE INDEX IF NOT EXISTS idx_source_records_status ON source_records(status);

-- 2. Content Items Table
CREATE TABLE IF NOT EXISTS content_items (
    id VARCHAR(36) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    arabic_text TEXT NOT NULL,
    english_meaning TEXT NOT NULL,
    transliteration TEXT,
    caption_ar TEXT,
    caption_en TEXT,
    source_id VARCHAR(36) NOT NULL REFERENCES source_records(id) ON DELETE CASCADE,
    verification_status VARCHAR(50) NOT NULL DEFAULT 'UNVERIFIED',
    approval_status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_content_items_category ON content_items(category);
CREATE INDEX IF NOT EXISTS idx_content_items_source_id ON content_items(source_id);
CREATE INDEX IF NOT EXISTS idx_content_items_verification ON content_items(verification_status);
CREATE INDEX IF NOT EXISTS idx_content_items_approval ON content_items(approval_status);
CREATE INDEX IF NOT EXISTS idx_content_items_is_demo ON content_items(is_demo);

-- 3. Media Assets Table
CREATE TABLE IF NOT EXISTS media_assets (
    id VARCHAR(36) PRIMARY KEY,
    content_id VARCHAR(36) NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    asset_type VARCHAR(50) NOT NULL,
    storage_url VARCHAR(1024) NOT NULL,
    local_path VARCHAR(512),
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_media_assets_content_id ON media_assets(content_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_type ON media_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_media_assets_checksum ON media_assets(checksum);

-- 4. Publication Jobs Table
CREATE TABLE IF NOT EXISTS publication_jobs (
    id VARCHAR(36) PRIMARY KEY,
    content_id VARCHAR(36) NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL DEFAULT 'instagram',
    publication_type VARCHAR(50) NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    instagram_media_id VARCHAR(100),
    last_error TEXT,
    claimed_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_publication_jobs_content_id ON publication_jobs(content_id);
CREATE INDEX IF NOT EXISTS idx_publication_jobs_type ON publication_jobs(publication_type);
CREATE INDEX IF NOT EXISTS idx_publication_jobs_status ON publication_jobs(status);
CREATE INDEX IF NOT EXISTS idx_publication_jobs_due ON publication_jobs(status, scheduled_at);

-- 5. Publication Attempts Table
CREATE TABLE IF NOT EXISTS publication_attempts (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES publication_jobs(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    request_started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_received_at TIMESTAMPTZ,
    response_status INTEGER,
    error_category VARCHAR(50),
    error_message_redacted TEXT
);

CREATE INDEX IF NOT EXISTS idx_publication_attempts_job_id ON publication_attempts(job_id);

-- 6. Application Settings Table
CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
