--  models/marts/dim_product.sql



select
    distinct stock_code,    -- dedupe each product
    description    -- Human readable text about the product
from online_retail."staging"."stg_online_retail"