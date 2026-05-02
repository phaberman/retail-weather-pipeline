with base as (
  select * from {{ ref('stg_weather') }}
)

select
  date,
  city,
  temp_max_f,
  temp_min_f,
  precipitation_in,
  windspeed_max_mph,
  is_rainy_day,
  is_freezing_day,
  is_hot_day,
  is_windy_day,
  (
    case when is_freezing_day then 1 else 0 end +
    case when is_hot_day      then 1 else 0 end +
    case when is_rainy_day    then 1 else 0 end +
    case when is_windy_day    then 1 else 0 end
    ) as alert_score
  from
    base
  where
    is_rainy_day or is_freezing_day or is_hot_day or is_windy_day
  order by
    date desc,
    alert_score desc
