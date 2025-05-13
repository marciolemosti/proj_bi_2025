-- models/staging/stg_cambio_ptax_venda.sql

with source as (

    select * from {{ source("public", "cambio_ptax_venda") }}

),

renamed as (

    select
        data as data_referencia,
        valor as cambio_ptax_venda_brl_usd

    from source

)

select * from renamed
