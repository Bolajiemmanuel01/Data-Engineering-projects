
  
    

  create  table online_retail."staging"."stg_online_retail__dbt_tmp"
  
  
    as
  
  (
    -- models/stg_online_retail.sql

  
-- We materialize as a table so downstream models and tests run faster and only rebuild when changed.

select
  "Invoice"::text           as invoice_no,    -- Raw column is named "Invoice" (uppercase), so we quote it; cast to text and rename to snake_case.
  "StockCode"               as stock_code,    -- Quote because original has uppercase letters; rename to snake_case.
  "Description"             as description,   -- Keep original text column; rename to lowercase for consistency.
  "Quantity"                as quantity,      -- Numeric column; rename to lowercase.
  "InvoiceDate"::timestamp  as invoice_date,  -- Quote and cast string to timestamp to enable date functions.
  "Price"                   as unit_price,    -- Original column named "Price"; rename to unit_price to reflect what it is.
  "Customer ID"             as customer_id,   -- Quotes required because of the space; rename to snake_case.
  "Country"                 as country        -- Geographic column; rename to lowercase.
from "online_retail"."staging"."online_retail_raw"
-- We reference the raw table via source(), so dbt knows lineage and can generate docs/tests.
  );
  