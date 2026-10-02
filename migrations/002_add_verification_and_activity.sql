-- Migration 002: Add email/phone verification columns to users and create learning_activities table

-- Add email verification columns to users
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255),
    ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS email_verification_sent_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50),
    ADD COLUMN IF NOT EXISTS is_phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS phone_otp_hash VARCHAR(255),
    ADD COLUMN IF NOT EXISTS phone_otp_expires_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS phone_otp_sent_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS phone_otp_attempts INTEGER NOT NULL DEFAULT 0;

-- Index verification token for fast lookups
CREATE INDEX IF NOT EXISTS ix_users_email_verification_token ON users (email_verification_token);

-- Create learning_activities table for tracking daily learning actions and calculating streaks
CREATE TABLE IF NOT EXISTS learning_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_learning_activities_user_id ON learning_activities (user_id);
CREATE INDEX IF NOT EXISTS ix_learning_activities_activity_date ON learning_activities (activity_date);

