--  models/marts/dim_product.sql

{{ config(materialized='table') }}

select
    distinct stock_code,    -- dedupe each product
    description    -- Human readable text about the product
from {{ ref('stg_online_retail') }}