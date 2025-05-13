WITH source AS (
    SELECT
        data AS data_referencia,
        valor AS pib_valor_corrente_brl_milhoes
    FROM
        {{ source('public', 'pib_trimestral') }}
)
SELECT
    data_referencia,
    pib_valor_corrente_brl_milhoes
FROM
    source
ORDER BY
    data_referencia

