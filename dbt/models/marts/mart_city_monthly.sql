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
  d.year,
  d.month_num,
  d.month_name,
  d.season,

  -- Temperature
  round(avg(fct.temp_avg_f), 2) as avg_temp_f,
  round(avg(fct.temp_max_f), 2) as avg_high_f,
  round(avg(fct.temp_min_f), 2) as avg_low_f,

  -- Precipitation
  round(sum(fct.precipitation_in), 2) as total_precipitation_in,

  -- Weather impact day counts
  countif(fct.is_rainy_day) as rainy_days,
  countif(fct.is_freezing_day) as freezing_days,
  countif(fct.is_hot_day) as hot_days,
  countif(fct.is_windy_day) as windy_days,
  countif(fct.alert_score > 0) as total_weather_impact_days

from
  fct
left join
  dim_date as d on fct.date_key = d.date_key
left join
  dim_city as c on fct.city_key = c.city_key

group by
  c.city_name,
  c.region,
  c.climate_zone,
  d.year,
  d.month_num,
  d.month_name,
  d.season
