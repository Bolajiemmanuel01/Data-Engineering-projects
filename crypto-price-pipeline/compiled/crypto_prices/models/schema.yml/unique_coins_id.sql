
    
    

select
    id as unique_field,
    count(*) as n_records

from "crypto"."public_silver"."coins"
where id is not null
group by id
having count(*) > 1


