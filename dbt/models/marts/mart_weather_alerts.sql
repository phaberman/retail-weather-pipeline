with fct as (

  select * from {{ ref('fct_weather') }}

),

dim_date as (

  select * from {{ ref('dim_date') }}

),

dim_city as (

  select * from {{ ref('dim_city') }}

)

select
  c.city_name,
  c.region,
  c.climate_zone,
  d.full_date,
  d.year,
  d.month_name,
  d.season,
  d.is_weekend,

  -- Measures
  fct.temp_max_f,
  fct.temp_min_f,
  fct.precipitation_in,
  fct.windspeed_max_mph,

  -- Flags
  fct.is_rainy_day,
  fct.is_freezing_day,
  fct.is_hot_day,
  fct.is_windy_day,

  -- Alert score
  fct.alert_score

from
  fct
left join
  dim_date as d on fct.date_key = d.date_key
left join
  dim_city as c on fct.city_key = c.city_key

where
  fct.alert_score > 0

order by
  d.full_date desc,
  fct.alert_score desc
