
select
  retrieved_at,
  coin_id,
  vs_currency,
  price,
  market_cap,
  volume_24h
from "crypto"."public_silver"."stg_crypto_prices"

where retrieved_at > (select coalesce(max(retrieved_at), '1900-01-01') from "crypto"."public_gold"."fct_price_points")
