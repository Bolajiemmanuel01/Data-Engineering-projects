
  
    

  create  table "crypto"."public_gold"."fct_price_daily__dbt_tmp"
  
  
    as
  
  (
    
with points as (
  select * from "crypto"."public_gold"."fct_price_points"
),
daily as (
  select
    date_trunc('day', retrieved_at) as day,
    coin_id,
    vs_currency,
    avg(price) as avg_price,
    min(price) as min_price,
    max(price) as max_price,
    stddev_samp(price) as volatility,
    count(*) as points
  from points
  group by 1,2,3
),
with_prev as (
  select
    d.*,
    lag(avg_price) over (partition by coin_id, vs_currency order by day) as prev_avg_price
  from daily d
)
select
  *,
  case
    when prev_avg_price is null or prev_avg_price = 0 then null
    else round( (avg_price - prev_avg_price) / prev_avg_price * 100.0, 4)
  end as pct_change_vs_prev_day
from with_prev
  );
  