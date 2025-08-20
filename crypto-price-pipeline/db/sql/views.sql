-- Friendly view for dashboards (adds coin name)
CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE VIEW gold.vw_crypto_daily AS
SELECT
  d.day,
  d.coin_id,
  c.name AS coin_name,
  d.vs_currency,
  d.avg_price,
  d.min_price,
  d.max_price,
  d.volatility,
  d.pct_change_vs_prev_day
FROM gold.fct_price_daily d
LEFT JOIN silver.coins c
  ON c.id = d.coin_id;
