with date_spine as (

  select date
  from unnest(
      generate_date_array('2023-01-01', current_date())
  ) as date

)

select

  cast(format_date('%Y%m%d', date) as int64) as date_key,

  date as full_date,

  extract(year from date) as year,

  extract(month from date) as month_num,
  format_date('%B', date) as month_name,

  extract(quarter from date) as quarter,

  extract(week from date) as week_of_year,

  extract(dayofweek from date) as day_of_week_num,
  format_date('%A', date) as day_of_week_name,

  extract(day from date) as day_of_month,

  case
      when extract(dayofweek from date) in (1, 7) then true
      else false
  end as is_weekend,

  case
    when extract(month from date) in (1, 2, 12) then 'Winter'
    when extract(month from date) in (3, 4, 5) then 'Spring'
    when extract(month from date) in (6, 7, 8) then 'Summer'
    when extract(month from date) in (9, 10, 11) then 'Fall'
    else 'Unknown'
  end as season

from
  date_spine
