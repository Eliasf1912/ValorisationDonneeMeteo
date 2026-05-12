CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
   'refresh-mv-quotidienne-realtime',
   '*/6 * * * *',
   $$
   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_quotidienne_realtime;
   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_mensuelle_realtime;
   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_itn_daily_all_years;
   $$
);
