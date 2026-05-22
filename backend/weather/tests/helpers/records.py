"""
Helpers d'insertion pour la pipeline `mv_records_battus` :
- `mv_records_battus`       : table des records battus (recréée comme table
  régulière par le conftest pour permettre les INSERT directs).
- `mv_records_battus_meta`  : table de métadonnées contenant la `cutoff_date`.
"""

from __future__ import annotations

import datetime as dt

from django.db import connection


def insert_mv_record(
    station_code: str,
    station_name: str,
    period_type: str,
    period_value: str | None,
    record_type: str,
    value: float,
    date: dt.date,
    department: int = 75,
) -> None:
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.mv_records_battus
                (period_type,     period_value,     record_type,     station_code,     station_name,     department,     record_value,     record_date)
            VALUES
                (%(period_type)s, %(period_value)s, %(record_type)s, %(station_code)s, %(station_name)s, %(department)s, %(record_value)s, %(record_date)s)
            """,
            {
                "period_type": period_type,
                "period_value": period_value,
                "record_type": record_type,
                "station_code": station_code,
                "station_name": station_name,
                "department": department,
                "record_value": value,
                "record_date": date,
            },
        )


def set_cutoff(date: dt.date) -> None:
    with connection.cursor() as cur:
        cur.execute("TRUNCATE public.mv_records_battus_meta;")
        cur.execute(
            """
            INSERT INTO public.mv_records_battus_meta (cutoff_date)
            VALUES (%(cutoff_date)s);
            """,
            {"cutoff_date": date},
        )


def clear_mv() -> None:
    with connection.cursor() as cur:
        cur.execute("TRUNCATE public.mv_records_battus;")
        cur.execute("TRUNCATE public.mv_records_battus_meta;")
