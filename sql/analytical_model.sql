-- Portable analytical model for a warehouse or DuckDB-style environment.
-- Public tables must contain synthetic or approved de-identified data only.

with member_summary as (
    select
        household_id,
        count(*) as member_count,
        avg(case when literate = 1 then 1.0 else 0.0 end) as literacy_rate,
        avg(case when employed = 1 then 1.0 else 0.0 end) as employment_rate,
        sum(coalesce(personal_income_bob, 0)) as member_income_bob
    from members
    group by household_id
),
quality_flags as (
    select
        h.*,
        case when h.monthly_income_bob is null then 1 else 0 end as income_missing,
        case when h.household_size <> m.member_count then 1 else 0 end as member_count_mismatch
    from households h
    left join member_summary m using (household_id)
)
select
    q.household_id,
    q.zone,
    q.head_gender,
    q.household_size,
    q.housing_score,
    q.adequate_housing,
    q.vulnerability_index,
    q.monthly_income_bob,
    m.literacy_rate,
    m.employment_rate,
    q.income_missing,
    q.member_count_mismatch
from quality_flags q
left join member_summary m using (household_id);

