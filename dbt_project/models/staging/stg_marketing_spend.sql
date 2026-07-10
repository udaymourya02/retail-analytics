-- models/staging/stg_marketing_spend.sql
with source as (
    select * from {{ source('warehouse', 'fact_marketing_spend') }}
),
renamed as (
    select
        spend_key,
        date_key,
        campaign_key,
        impressions,
        clicks,
        round(spend_pence            / 100.0, 2) as spend_gbp,
        round(attributed_revenue_pence / 100.0, 2) as attributed_revenue_gbp,
        attributed_orders,
        ctr,
        round(cpc_pence / 100.0, 2)              as cpc_gbp,
        roas,
        source_system,
        pipeline_run_id,
        created_at
    from source
    where spend_key is not null
)
select * from renamed
