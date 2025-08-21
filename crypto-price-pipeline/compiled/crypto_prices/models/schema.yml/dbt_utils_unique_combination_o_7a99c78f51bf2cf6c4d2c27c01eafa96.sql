





with validation_errors as (

    select
        day, coin_id, vs_currency
    from "crypto"."public_gold"."fct_price_daily"
    group by day, coin_id, vs_currency
    having count(*) > 1

)

select *
from validation_errors


