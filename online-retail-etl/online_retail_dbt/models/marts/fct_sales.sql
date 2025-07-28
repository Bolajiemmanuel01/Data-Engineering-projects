-- models/marts/fct_sales.sql

{{ config(materialized='incremental', unique_key=['invoice_no','stock_code']) }}
-- Keep this fact incremental; dedupe on invoice_no + stock_code

select
  invoice_no,                             -- invoice identifier
  stock_code,                             -- product code
  customer_id,                            -- customer identifier
  invoice_date::date   as date_key,      -- FK to dim_date
  quantity,                               -- units sold
  unit_price,                             -- price at time of sale
  quantity * unit_price  as revenue       -- revenue measure
from {{ ref('stg_online_retail') }}       -- pulls from your staging model
{% if is_incremental() %}
  where invoice_date::date > (
    select max(date_key) from {{ this }}  -- only new dates since last run
  )
{% endif %}
