USE IDENTIFIER(:database);

-- drop table if exists dim_stores;
-- Stores table schema for BrickMart retail chain
CREATE TABLE IF NOT EXISTS dim_stores2 (
    store_id STRING NOT NULL COMMENT 'Unique identifier for each store location (e.g., 001, 002)',
    store_name STRING NOT NULL COMMENT 'Display name of the store location (e.g., Downtown, Uptown)',
    store_address STRING NOT NULL COMMENT 'Street address of the store location',
    store_city STRING NOT NULL COMMENT 'City where the store is located',
    store_state STRING NOT NULL COMMENT 'State or province abbreviation (e.g., NY, CA, TX)',
    store_zipcode STRING NOT NULL COMMENT 'Postal/ZIP code for the store location',
    store_country STRING NOT NULL COMMENT 'Country where the store is located (e.g., USA)',
    store_phone STRING COMMENT 'Primary phone number for customer contact',
    store_email STRING COMMENT 'Primary email address for customer contact',
    store_manager_id STRING COMMENT 'Employee ID of the store manager',
    opening_date DATE COMMENT 'Date when the store first opened for business',
    store_area_sqft DOUBLE COMMENT 'Total floor area of the store in square feet',
    is_open_24_hours BOOLEAN COMMENT 'Whether the store operates 24 hours a day (true/false)',
    latitude DOUBLE COMMENT 'Geographic latitude coordinate for store location',
    longitude DOUBLE COMMENT 'Geographic longitude coordinate for store location',
    region_id STRING COMMENT 'Regional identifier for grouping stores by geographic area',
    store_details_text STRING COMMENT 'Combined store information for text search and vector embeddings',
    created_at TIMESTAMP COMMENT 'Timestamp when the store record was created in the system',
    updated_at TIMESTAMP COMMENT 'Timestamp when the store record was last updated'
) 
USING DELTA
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.enableChangeDataFeed' = 'true'

);
