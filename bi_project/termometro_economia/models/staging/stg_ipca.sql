-- models/staging/stg_ipca.sql

with source as (

    select * from {{ source("public", "ipca") }}

),

renamed as (

    select
        data as data_referencia,
        valor as indice_ipca

    from source

)

select * from renamed
