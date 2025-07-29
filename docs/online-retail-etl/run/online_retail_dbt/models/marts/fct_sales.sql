
      
  
    

  create  table online_retail."staging_staging"."fct_sales"
  
  
    as
  
  (
    -- models/marts/fct_sales.sql


-- Keep this fact incremental; dedupe on invoice_no + stock_code

select
  invoice_no,                             -- invoice identifier
  stock_code,                             -- product code
  customer_id,                            -- customer identifier
  invoice_date::date   as date_key,      -- FK to dim_date
  quantity,                               -- units sold
  unit_price,                             -- price at time of sale
  quantity * unit_price  as revenue       -- revenue measure
from online_retail."staging"."stg_online_retail"       -- pulls from your staging model

  );
  
  