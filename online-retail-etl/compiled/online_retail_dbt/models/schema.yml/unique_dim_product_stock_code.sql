
    
    

select
    stock_code as unique_field,
    count(*) as n_records

from crypto."public_staging"."dim_product"
where stock_code is not null
group by stock_code
having count(*) > 1


