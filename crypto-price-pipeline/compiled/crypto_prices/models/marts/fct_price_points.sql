
select
  retrieved_at,
  coin_id,
  vs_currency,
  price,
  market_cap,
  volume_24h
from "crypto"."public_silver"."stg_crypto_prices"
