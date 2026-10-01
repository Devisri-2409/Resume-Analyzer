-- Run this once against the existing PostgreSQL database.
-- It preserves all existing users and assigns them the default user role.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';