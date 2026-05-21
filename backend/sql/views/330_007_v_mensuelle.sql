CREATE OR REPLACE VIEW public.v_mensuelle AS
WITH mensuelle_climato AS (
    SELECT
        "NUM_POSTE"                                                 AS station_code,
        "AAAAMM"                                                    AS date,
        "TNAB"                                                      AS tnn,
        ("AAAAMM" + ("TNDAT" - 1) * interval '1 day')::timestamp(3) AS tnn_date,
        "TXAB"                                                      AS txx,
        ("AAAAMM" + ("TXDAT" - 1) * interval '1 day')::timestamp(3) AS txx_date,
        "TM"                                                        AS tmm
    FROM "Mensuelle"
    WHERE "AAAAMM" < date_trunc('month', now()) - interval '2 months'
),
combined_mensuelle AS (
    SELECT station_code, date, tnn, tnn_date, txx, txx_date, tmm FROM public.mv_mensuelle_realtime
    UNION ALL
    SELECT station_code, date, tnn, tnn_date, txx, txx_date, tmm FROM mensuelle_climato
)
SELECT
    station_code,
    date,
    tnn,
    tnn_date,
    txx,
    txx_date,
    tmm
FROM combined_mensuelle;
