-- tests/assert_rfm_covers_all_customers.sql
-- ============================================================
-- Custom dbt Test: Every active customer must have an RFM score.
-- Finds customers who have made purchases but are missing from
-- the RFM mart — indicates a join or data gap.
-- ============================================================

with customers_with_purchases as (
    select distinct customer_id
    from {{ ref('int_customer_orders') }}
    where total_orders > 0
),

rfm_customers as (
    select distinct customer_id
    from {{ ref('mart_customer_rfm') }}
)

-- Any customer with purchases who is NOT in the RFM mart is a failure
select p.customer_id
from customers_with_purchases p
left join rfm_customers r on p.customer_id = r.customer_id
where r.customer_id is null
