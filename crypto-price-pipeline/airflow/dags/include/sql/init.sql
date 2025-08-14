-- Create schemas and raw table for crypto prices
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS bronze.crypto_prices_raw (
    id BIGSERIAL PRIMARY KEY,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(50) NOT NULL,
    vs_currency VARCHAR(10) NOT NULL,
    payload JSONB NOT NULL
);

-- Helpful index for time-based queries
CREATE INDEX IF NOT EXISTS idx_crypto_prices_raw_retrieved_at
    ON bronze.crypto_prices_raw (retrieved_at);
