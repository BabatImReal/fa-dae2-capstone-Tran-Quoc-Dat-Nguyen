{{ config(
  materialized='table',
  cluster_by=['primary_payment_type']
) }}

with payments as (
  select
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value,
    loaded_at
  from {{ ref('stg__order_payments') }}
),
-- totals by type per order to pick a primary method
type_totals as (
  select
    order_id,
    payment_type,
    sum(payment_value) as payment_value_sum,
    count(*) as payment_count,
    max(payment_installments) as max_installments_by_type
  from payments
  group by order_id, payment_type
),
primary_type as (
  select
    order_id,
    payment_type as primary_payment_type,
    row_number() over (
      partition by order_id
      order by payment_value_sum desc, payment_count desc, payment_type
    ) as rn
  from type_totals
),
order_agg as (
  select
    order_id,
    count(*) as num_payments,
    count(distinct payment_type) as payment_types_count,
    sum(payment_value) as total_payment_value,
    max(payment_installments) as max_installments,
    -- 1 if any installment > 1 in the order
    max(case when payment_installments > 1 then 1 else 0 end) as has_installments_flag,
    max(loaded_at) as loaded_at
  from payments
  group by order_id
)

select
  {{ dbt_utils.generate_surrogate_key(['oa.order_id', 'oa.loaded_at']) }} as order_payment_key,
  oa.order_id,
  pt.primary_payment_type,
  oa.payment_types_count,
  oa.num_payments,
  oa.total_payment_value,
  oa.max_installments,
  oa.has_installments_flag,
  oa.loaded_at
from order_agg oa
left join primary_type pt
  on oa.order_id = pt.order_id
  and pt.rn = 1
