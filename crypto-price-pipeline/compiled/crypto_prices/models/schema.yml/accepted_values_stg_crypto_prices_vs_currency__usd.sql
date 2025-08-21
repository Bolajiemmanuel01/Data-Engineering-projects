
    
    

with all_values as (

    select
        vs_currency as value_field,
        count(*) as n_records

    from "crypto"."public_silver"."stg_crypto_prices"
    group by vs_currency

)

select *
from all_values
where value_field not in (
    'usd'
)


