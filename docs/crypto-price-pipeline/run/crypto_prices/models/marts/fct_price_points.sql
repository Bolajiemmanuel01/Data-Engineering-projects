
      
        
            delete from "crypto"."public_gold"."fct_price_points"
            using "fct_price_points__dbt_tmp120039835505"
            where (
                
                    "fct_price_points__dbt_tmp120039835505".retrieved_at = "crypto"."public_gold"."fct_price_points".retrieved_at
                    and 
                
                    "fct_price_points__dbt_tmp120039835505".coin_id = "crypto"."public_gold"."fct_price_points".coin_id
                    and 
                
                    "fct_price_points__dbt_tmp120039835505".vs_currency = "crypto"."public_gold"."fct_price_points".vs_currency
                    
                
                
            );
        
    

    insert into "crypto"."public_gold"."fct_price_points" ("retrieved_at", "coin_id", "vs_currency", "price", "market_cap", "volume_24h")
    (
        select "retrieved_at", "coin_id", "vs_currency", "price", "market_cap", "volume_24h"
        from "fct_price_points__dbt_tmp120039835505"
    )
  