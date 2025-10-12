-- db_schema.sql
-- Schema for PhonePe Transaction Insights
-- Works for PostgreSQL. For SQLite minor tweaks (serial -> integer primary key autoincrement).

-- Aggregated_user: aggregated user metrics (per region/time)
CREATE TABLE IF NOT EXISTS aggregated_user (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    quarter TEXT,
    level TEXT,           -- country/state/district
    state TEXT,
    district TEXT,
    registered_users BIGINT,
    app_opens BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Aggregated_transaction: aggregated transaction metrics (for choropleth)
CREATE TABLE IF NOT EXISTS aggregated_transaction (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    quarter TEXT,
    level TEXT,           -- country/state/district
    state TEXT,
    district TEXT,
    txn_type TEXT,
    count BIGINT,
    amount NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Aggregated_insurance: aggregated insurance data
CREATE TABLE IF NOT EXISTS aggregated_insurance (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    quarter TEXT,
    level TEXT,
    state TEXT,
    district TEXT,
    insurance_type TEXT,
    count BIGINT,
    amount NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Map tables (store geo-values aggregated for maps)
CREATE TABLE IF NOT EXISTS map_values (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    quarter TEXT,
    level TEXT,     -- state/district
    state TEXT,
    district TEXT,
    total_amount NUMERIC,
    total_count BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Top tables (top states/districts/pincodes)
CREATE TABLE IF NOT EXISTS top_map (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    quarter TEXT,
    category TEXT,  -- transaction/user/insurance
    level TEXT,     -- state/district/pincode
    region TEXT,
    count BIGINT,
    amount NUMERIC,
    rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
