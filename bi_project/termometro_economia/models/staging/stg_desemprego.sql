-- models/staging/stg_desemprego.sql

with source as (

    select * from {{ source('public', 'desemprego') }}

),

renamed as (

    select
        data as data_referencia,
        valor as taxa_desemprego_percentual

    from source

)

select * from renamed

