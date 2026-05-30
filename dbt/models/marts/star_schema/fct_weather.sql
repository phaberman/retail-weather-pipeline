with stg as (

    select * from {{ ref('stg_weather') }}

),

dim_date as (

    select * from {{ ref('dim_date') }}

),

dim_city as (

    select * from {{ ref('dim_city') }}

)

select

    -- Surrogate keys (FK)
    d.date_key,
    c.city_key,

    -- Natural keys
    stg.date,
    stg.city,

    -- Temperature measures
    stg.temp_max_f,
    stg.temp_min_f,
    stg.temp_avg_f,

    -- Precipitation measures
    stg.precipitation_in,

    -- Wind measures
    stg.windspeed_max_mph,

    -- Weather code
    stg.wmo_code,

    -- Retail impact flags
    stg.is_rainy_day,
    stg.is_freezing_day,
    stg.is_hot_day,
    stg.is_windy_day,

    -- Alert score
    (case when stg.is_freezing_day then 1 else 0 end +
     case when stg.is_hot_day      then 1 else 0 end +
     case when stg.is_rainy_day    then 1 else 0 end +
     case when stg.is_windy_day    then 1 else 0 end) as alert_score

from stg
left join dim_date as d on stg.date = d.full_date
left join dim_city as c on stg.city = c.city
