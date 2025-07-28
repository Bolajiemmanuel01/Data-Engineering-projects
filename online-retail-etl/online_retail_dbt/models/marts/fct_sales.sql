-- models/marts/fct_sales.sql

{{ 
  config(
    materialized='incremental',               -- use incremental loads 
    unique_key=['invoice_no', 'stock_code']   -- composite key to identify new rows
  ) 
}}  

select
  invoice_no,
  stock_code,                as product_code
  customer_id,
  invoice_date::date         as date_key,   -- FK to dim_date.date_key
  quantity,
  unit_price,
  quantity * unit_price      as revenue
from {{ ref('stg_online_retail') }}
{% if is_incremental() %}
  -- only select rows newer than the max loaded date_key
  where invoice_date::date > (
    select max(date_key) from {{ this }}
  )
{% endif %}