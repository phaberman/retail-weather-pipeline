with cities as (

  select distinct city from {{ ref('stg_weather') }}

)

select
  -- Surrogate key
  row_number() over (order by city) as city_key,

  -- Natural key
  city,

  -- Attributes
  case city
      when 'new_york'     then 'New York'
      when 'chicago'      then 'Chicago'
      when 'los_angeles'  then 'Los Angeles'
      when 'houston'      then 'Houston'
      when 'seattle'      then 'Seattle'
  end as city_name,

  case city
      when 'new_york'     then 'Northeast'
      when 'chicago'      then 'Midwest'
      when 'los_angeles'  then 'West'
      when 'houston'      then 'South'
      when 'seattle'      then 'Northwest'
  end as region,

  case city
      when 'new_york'     then 'Humid Continental'
      when 'chicago'      then 'Humid Continental'
      when 'los_angeles'  then 'Mediterranean'
      when 'houston'      then 'Humid Subtropical'
      when 'seattle'      then 'Oceanic'
  end as climate_zone

from
  cities
