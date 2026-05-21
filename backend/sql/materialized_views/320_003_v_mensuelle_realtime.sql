CREATE OR REPLACE VIEW public.v_mensuelle_realtime AS
WITH ranked AS (
    SELECT
        station_code,
        date_trunc('month', date) AS month_date,
        date                      AS daily_date,
        tn,
        tx,
        tntxm,
        ROW_NUMBER() OVER (
            PARTITION BY station_code, date_trunc('month', date)
            ORDER BY tn ASC NULLS LAST, date ASC
        ) AS rn_tn_min,
        ROW_NUMBER() OVER (
            PARTITION BY station_code, date_trunc('month', date)
            ORDER BY tx DESC NULLS LAST, date ASC
        ) AS rn_tx_max
    FROM public.v_quotidienne
    WHERE date >= date_trunc('month', now()) - interval '2 months'
)
SELECT
    station_code,
    month_date                                                          AS date,
    MIN(tn)                                                             AS tnn,
    MAX(CASE WHEN rn_tn_min = 1 AND tn IS NOT NULL THEN daily_date END) AS tnn_date,
    MAX(tx)                                                             AS txx,
    MAX(CASE WHEN rn_tx_max = 1 AND tx IS NOT NULL THEN daily_date END) AS txx_date,
    ROUND(AVG(tntxm)::numeric, 1)                                       AS tmm
FROM ranked
GROUP BY station_code, month_date;
