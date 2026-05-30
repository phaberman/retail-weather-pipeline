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
  -- City attributes
  c.city_name,
  c.region,
  c.climate_zone,

  -- Date attributes
  d.full_date,
  d.year,
  d.month_num,
  d.month_name,
  d.season,
  d.is_weekend,
  d.day_of_week_name,

  -- Temperature
  fct.temp_max_f,
  fct.temp_min_f,
  fct.temp_avg_f,

  -- Precipitation
  fct.precipitation_in,

  -- Wind
  fct.windspeed_max_mph,

  -- Weather code
  fct.wmo_code,

  -- Retail flags
  fct.is_rainy_day,
  fct.is_freezing_day,
  fct.is_hot_day,
  fct.is_windy_day,
  fct.alert_score

from
  fct
left join
  dim_date as d on fct.date_key = d.date_key
left join
  dim_city as c on fct.city_key = c.city_key

order by
  d.full_date desc,
  c.city_name
