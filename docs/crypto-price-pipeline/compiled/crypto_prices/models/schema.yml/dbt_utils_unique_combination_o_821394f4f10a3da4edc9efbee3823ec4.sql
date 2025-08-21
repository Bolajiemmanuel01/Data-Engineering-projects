





with validation_errors as (

    select
        retrieved_at, coin_id, vs_currency
    from "crypto"."public_gold"."fct_price_points"
    group by retrieved_at, coin_id, vs_currency
    having count(*) > 1

)

select *
from validation_errors


