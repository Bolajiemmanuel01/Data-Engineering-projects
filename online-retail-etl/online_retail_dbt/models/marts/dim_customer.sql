-- models/marts/dim_customer.sql

{{ config(materialized='table') }}

select
    distinct customer_id            as customer_id,     --One row per customer
    country                         as country          --Geographic attribute
from {{ ref('stg_online_retail') }}
where customer_id is not null       -- drop anonymous orders