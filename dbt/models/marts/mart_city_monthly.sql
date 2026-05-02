with base as (
  select * from {{ ref('stg_weather') }}
  )

select
  city,
  date_trunc(date, month) as month,
  round(avg(temp_avg_f), 2) as avg_temp_f,
  round(avg(temp_max_f), 2) as avg_high_f,
  round(avg(temp_min_f), 2) as avg_low_f,
  round(sum(precipitation_in), 2) as total_precipitation_in,
  countif(is_rainy_day) as rainy_days,
  countif(is_freezing_day) as freezing_days,
  countif(is_hot_day) as hot_days,
  countif(is_windy_day) as windy_days,
  countif(is_rainy_day or is_freezing_day or is_hot_day or is_windy_day) as total_weather_impact_days
from
  base
group by
  city,
  date_trunc(date, month)
