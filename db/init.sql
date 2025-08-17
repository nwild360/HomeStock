-- bootstrap the database with db schema
BEGIN;

CREATE schema IF NOT EXISTS homestock AUTHORIZATION CURRENT_USER; -- Create Schema and Make the user running this script the owner of the homestock schema

SET search_path = homestock, pg_catalog; -- ensures unqualified names resolve to homestock only (then system catalog).

CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- fast fuzzy search
CREATE EXTENSION IF NOT EXISTS pgcrypto;    -- gen_random_uuid() if we add public IDs later
CREATE EXTENSION IF NOT EXISTS unaccent;    -- optional: accent-insensitive search

-- Domain for item types
CREATE DOMAIN homestock.item_type AS TEXT
  CHECK (lower(VALUE) IN ('food','household','equipment'));

-- Mild hardening: don’t let “public” create objects in public schema
REVOKE CREATE ON SCHEMA public FROM PUBLIC;


-- ========= Table Definitions ==========
-- Create categories table
CREATE TABLE IF NOT EXISTS homestock.categories (
	id BIGSERIAL PRIMARY KEY,
	name TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 255),
	description TEXT CHECK (length(description) <= 1000)
);

-- Create items table
CREATE TABLE IF NOT EXISTS homestock.items (
	id BIGSERIAL PRIMARY KEY,
	name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 255),
	type homestock.item_type NOT NULL,
	category_id BIGINT REFERENCES homestock.categories(id) ON DELETE SET NULL,
	mealie_food_id TEXT UNIQUE CHECK (mealie_food_id ~ '^[A-Za-z0-9\-_]{1,64}$'),
	notes TEXT CHECK (length(notes) <= 1000),
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create units table
CREATE TABLE IF NOT EXISTS homestock.units (
	id BIGSERIAL PRIMARY KEY,
	name TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 255),
	abbreviation TEXT UNIQUE
);

-- Create item_stock table
CREATE TABLE IF NOT EXISTS homestock.item_stock (
	id BIGINT PRIMARY KEY REFERENCES homestock.items(id) ON DELETE CASCADE,
	unit_id BIGINT REFERENCES homestock.units(id) ON DELETE SET NULL,
	quantity NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========== Indexes ==========
-- Helpful index for the foreign keys
CREATE INDEX IF NOT EXISTS idx_items_category_id ON homestock.items (category_id);
CREATE INDEX IF NOT EXISTS idx_item_stock_unit_id ON homestock.item_stock (unit_id);
CREATE INDEX IF NOT EXISTS idx_items_name_trgm
ON homestock.items USING gin (name gin_trgm_ops);

-- ========== Triggers ==========
-- Create a trigger function to update the updated_at column
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

CREATE TRIGGER update_item_stock_updated_at
BEFORE UPDATE ON homestock.item_stock
FOR EACH ROW
EXECUTE FUNCTION homestock.update_updated_at_column();

COMMIT;