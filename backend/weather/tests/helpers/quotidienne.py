"""
Helper d'insertion dans la table source `Quotidienne` (variante avec TX/TN).

Cette variante prend `tx` / `tn` et dérive `tntxm = (tx + tn) / 2`, comme
le calcul SQL. Pour les tests qui n'ont besoin que de la valeur agrégée
`TNTXM`, voir `weather.tests.helpers.itn.insert_quotidienne`.
"""

from __future__ import annotations

import datetime as dt

from django.db import connection


def insert_quotidienne(
    day: dt.date,
    code: str,
    *,
    tx: float | None = None,
    tn: float | None = None,
) -> None:
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO public."Quotidienne"
                ("NUM_POSTE", "NOM_USUEL", "LAT", "LON", "ALTI", "AAAAMMJJ", "TX", "TN", "TNTXM")
            VALUES
                (%(code)s, %(name)s, 0, 0, 0, %(day)s, %(tx)s, %(tn)s, %(tntxm)s)
            ON CONFLICT ("NUM_POSTE", "AAAAMMJJ")
            DO UPDATE SET "TX" = EXCLUDED."TX", "TN" = EXCLUDED."TN", "TNTXM" = EXCLUDED."TNTXM"
            """,
            {
                "code": code,
                "name": f"ST {code}",
                "day": day,
                "tx": tx,
                "tn": tn,
                "tntxm": (tx + tn) / 2 if tx is not None and tn is not None else None,
            },
        )
