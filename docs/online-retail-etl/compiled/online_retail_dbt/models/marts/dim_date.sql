-- models/marts/dim_date.sql

  


select
  invoice_date::date                      as date_key,    -- the surrogate key for the date
  extract(year  from invoice_date)        as year,        -- reporting year
  extract(month from invoice_date)        as month,       -- reporting month
  extract(day   from invoice_date)        as day,         -- day of month
  to_char(invoice_date, 'Day')            as weekday     -- name of the weekday

from (
  select distinct invoice_date
  from online_retail."staging"."stg_online_retail"
) raw_dates
order by date_key