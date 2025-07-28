--  models/marts/dim_product.sql

{{ config(materialized='table') }}

select
    distinct stock_code         as product_code,    -- dedupe each product
    description                 as product_name,    -- Human readable text about the product
from {{ ref('stg_online_retail') }}
where stock_code is not null