-- models/staging/stg_selic.sql

with source as (

    select * from {{ source('public', 'selic') }}

),

renamed as (

    select
        data as data_referencia,
        valor as taxa_selic_percentual

    from source

)

select * from renamed
