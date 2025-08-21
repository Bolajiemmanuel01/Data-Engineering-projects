
    
    

with child as (
    select coin_id as from_field
    from "crypto"."public_silver"."stg_crypto_prices"
    where coin_id is not null
),

parent as (
    select id as to_field
    from "crypto"."public_silver"."coins"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


