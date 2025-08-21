
with raw as (
  select
    id as raw_id,
    retrieved_at,
    vs_currency,
    jsonb_each(payload) as kv
  from "crypto"."bronze"."crypto_prices_raw"
),
expanded as (
  select
    raw_id,
    retrieved_at,
    vs_currency,
    (kv).key as coin_id,
    (kv).value as coin_metrics
  from raw
)
select
  raw_id,
  retrieved_at,
  coin_id,
  vs_currency,
  (coin_metrics ->> vs_currency)::numeric as price,
  (coin_metrics ->> (vs_currency || '_market_cap'))::numeric as market_cap,
  (coin_metrics ->> (vs_currency || '_24h_vol'))::numeric as volume_24h
from expanded