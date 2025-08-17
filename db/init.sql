-- bootstrap the database with db schema
BEGIN;

CREATE schema IF NOT EXISTS homestock AUTHORIZATION CURRENT_USER; -- Create Schema and Make the user running this script the owner of the homestock schema

ALTER DATABASE CURRENT_DATABASE() SET search_path = homestock, pg_catalog; -- ensures unqualified names resolve to homestock only (then system catalog).

CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- fast fuzzy search
CREATE EXTENSION IF NOT EXISTS pgcrypto;    -- gen_random_uuid() if we add public IDs later
CREATE EXTENSION IF NOT EXISTS unaccent;    -- optional: accent-insensitive search

-- Mild hardening: don’t let “public” create objects in public schema
REVOKE CREATE ON SCHEMA public FROM PUBLIC;


-- ========= Table Definitions ==========
-- Create categories table
CREATE TABLE IF NOT EXISTS homestock.categories (
	id BIGSERIAL PRIMARY KEY,
	name TEXT NOT NULL UNIQUE,
	description TEXT
);

-- Create items table
CREATE TABLE IF NOT EXISTS homestock.items (
	id BIGSERIAL PRIMARY KEY,
	name TEXT NOT NULL,
	type TEXT,
	category_id BIGINT REFERENCES homestock.categories(id) ON DELETE SET NULL,
	mealie_food_id TEXT UNIQUE, -- Mealie food ID for integration
	notes TEXT,
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create units table
CREATE TABLE IF NOT EXISTS homestock.units (
	id BIGSERIAL PRIMARY KEY,
	name TEXT NOT NULL UNIQUE,
	abbreviation TEXT UNIQUE,
);

-- Create item_stock table
CREATE TABLE IF NOT EXISTS homestock.item_stock (
	id BIGSERIAL PRIMARY KEY REFERENCES homestock.items(id) ON DELETE CASCADE,
	unit_id BIGINT REFERENCES homestock.units(id) ON DELETE SET NULL,
	quantity NUMERIC(10,2) NOT NULL CHECK ,
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========== Indexes ==========
-- Helpful index for the foreign key
CREATE INDEX IF NOT EXISTS idx_items_category_id ON homestock.items (category_id);


-- ========== Triggers ==========
-- Create a trigger function to update the updated_at column
CREATE OR REPLACE FUNCTION homestock.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
	NEW.updated_at = NOW();
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to call the function before each update
CREATE TRIGGER update_items_updated_at
BEFORE UPDATE ON homestock.items
FOR EACH ROW
EXECUTE FUNCTION homestock.update_updated_at_column();

