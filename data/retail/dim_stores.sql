USE IDENTIFIER(:database);
-- Stores table schema for BrickMart retail chain
CREATE TABLE IF NOT EXISTS dim_stores (
    store_id STRING NOT NULL,
    store_name STRING NOT NULL,
    store_address STRING NOT NULL,
    store_city STRING NOT NULL,
    store_state STRING NOT NULL,
    store_zipcode STRING NOT NULL,
    store_country STRING NOT NULL,
    store_phone STRING,
    store_email STRING,
    store_manager_id STRING,
    opening_date DATE,
    store_area_sqft DOUBLE,
    is_open_24_hours BOOLEAN,
    latitude DOUBLE,
    longitude DOUBLE,
    region_id STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) 
USING DELTA
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);
