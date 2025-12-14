-- bootstrap the database with db schema
BEGIN;

CREATE schema IF NOT EXISTS homestock AUTHORIZATION CURRENT_USER; -- Create Schema and Make the user running this script the owner of the homestock schema

SET search_path = homestock, pg_catalog; -- ensures unqualified names resolve to homestock only (then system catalog).

CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- fast fuzzy search for item name search

-- Domain for item types
CREATE DOMAIN homestock.item_type AS TEXT
  CHECK (lower(VALUE) IN ('food','household'));

-- Mild hardening: don't let "public" create objects in public schema
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- ========= Table Definitions ==========
-- Create users table first
CREATE TABLE IF NOT EXISTS homestock.users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE CHECK ( 
        length(username) BETWEEN 3 AND 50 AND
        username ~ '^[a-zA-Z0-9_-]+$'  -- alphanumeric, underscore, hyphen only
    ),
    hashed_password TEXT NOT NULL CHECK (length(hashed_password) >= 80)  -- argon2 hashes are ~90 chars
);

-- Create categories table second (referenced by items)
CREATE TABLE IF NOT EXISTS homestock.categories (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 255),
    description TEXT CHECK (length(description) <= 1000)
);

-- Create units table second (referenced by items)
CREATE TABLE IF NOT EXISTS homestock.units (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 255),
    abbreviation TEXT UNIQUE
);

-- Create items table last (after its dependencies)
CREATE TABLE IF NOT EXISTS homestock.items (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 255),
    type homestock.item_type NOT NULL,
    category_id BIGINT REFERENCES homestock.categories(id) ON DELETE SET NULL,
    quantity NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    unit_id BIGINT REFERENCES homestock.units(id) ON DELETE SET NULL,
    notes TEXT CHECK (length(notes) <= 1000),
    mealie_food_id TEXT UNIQUE CHECK (mealie_food_id ~ '^[A-Za-z0-9\-_]{1,64}$'),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- JWT Blacklist table for token revocation
CREATE TABLE IF NOT EXISTS homestock.jwt_blacklist (
    jti TEXT PRIMARY KEY,  -- JWT ID (unique identifier for each token)
    username TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========== Indexes ==========
-- Note: username index not needed - UNIQUE constraint on users.username automatically creates an index

-- Indexes for foreign keys
CREATE INDEX IF NOT EXISTS idx_items_category_id ON homestock.items (category_id);
CREATE INDEX IF NOT EXISTS idx_items_unit_id ON homestock.items (unit_id);
CREATE INDEX IF NOT EXISTS idx_items_name_trgm ON homestock.items USING gin (name gin_trgm_ops);

-- JWT blacklist indexes
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_expires_at ON homestock.jwt_blacklist (expires_at);
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_username ON homestock.jwt_blacklist (username);

-- ========== Triggers ==========
CREATE OR REPLACE FUNCTION homestock.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    EXCEPTION
        WHEN OTHERS THEN
            -- Log the error to the PostgreSQL log
            RAISE WARNING 'Error in update_updated_at_column trigger: %', SQLERRM;
            -- Optionally, re-raise or handle as needed
            RETURN NEW;
    END;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to call the function before each update
CREATE TRIGGER update_items_updated_at
    BEFORE UPDATE ON homestock.items
    FOR EACH ROW
    EXECUTE FUNCTION homestock.update_updated_at_column();

-- ========== JWT Blacklist Functions ==========
-- Auto-cleanup function: Delete expired tokens from blacklist
CREATE OR REPLACE FUNCTION homestock.cleanup_expired_jwt_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM homestock.jwt_blacklist
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

COMMIT;