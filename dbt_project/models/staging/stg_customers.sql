-- models/staging/stg_customers.sql
with source as (
    select * from {{ source('warehouse', 'dim_customer') }}
),
renamed as (
    select
        customer_key,
        customer_id,
        email_masked,
        age_band,
        gender,
        city,
        region,
        postcode_district,
        acquisition_channel,
        acquisition_date,
        loyalty_tier,
        rfm_recency_score,
        rfm_frequency_score,
        rfm_monetary_score,
        rfm_segment,
        rfm_updated_at,
        customer_ltv_gbp,
        is_current,
        valid_from,
        valid_to,
        created_at,
        updated_at
    from source
    where customer_key is not null
      and is_current = true    -- only current SCD Type 2 records
)
select * from renamed
