{{ config(materialized='incremental', unique_key=['retrieved_at','coin_id','vs_currency']) }}
select
  retrieved_at,
  coin_id,
  vs_currency,
  price,
  market_cap,
  volume_24h
from {{ ref('stg_crypto_prices') }}
{% if is_incremental() %}
where retrieved_at > (select coalesce(max(retrieved_at), '1900-01-01') from {{ this }})
{% endif %}
