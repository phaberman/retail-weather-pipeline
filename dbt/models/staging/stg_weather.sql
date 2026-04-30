with source as (
    select
        city,
        date,
        temperature_2m_max,
        temperature_2m_min,
        precipitation_sum,
        windspeed_10m_max,
        weathercode
    from {{ source('raw', 'weather') }}
),

renamed as (
    select
        city,
        date,

        -- Temperature
        temperature_2m_max as temp_max_f,
        temperature_2m_min as temp_min_f,
        round((temperature_2m_max + temperature_2m_min) / 2, 2) as temp_avg_f,

        -- Precipitation
        precipitation_sum as precipitation_in,

        -- Wind
        windspeed_10m_max as windspeed_max_mph,

        -- Weather code
        weathercode as wmo_code,

        -- Retail weather flags
        case when precipitation_sum > 0.1  then true else false end as is_rainy_day,
        case when temperature_2m_max < 32  then true else false end as is_freezing_day,
        case when temperature_2m_max > 90  then true else false end as is_hot_day,
        case when windspeed_10m_max > 25   then true else false end as is_windy_day

    from source
)

select * from renamed
