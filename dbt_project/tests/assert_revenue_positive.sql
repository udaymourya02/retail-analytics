-- tests/assert_revenue_positive.sql
-- ============================================================
-- Custom dbt Test: Revenue Must Be Positive
-- Checks that no mart table contains negative net revenue rows.
-- If this returns any rows, the test FAILS.
-- ============================================================

select
    sale_key,
    order_id,
    net_revenue_gbp
from {{ ref('stg_sales') }}
where net_revenue_gbp < 0
  and is_returned = false
