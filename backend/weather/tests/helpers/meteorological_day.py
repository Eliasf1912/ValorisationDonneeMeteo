"""
Helpers purement Python (sans dépendance Django) reproduisant la convention
SQL de journée météorologique utilisée par `v_quotidienne_realtime` :

- `tn(D)` = MIN sur la fenêtre (D-1 18:00:01 → D 18:00:00)
- `tx(D)` = MAX sur la fenêtre (D 06:00:01 → D+1 06:00:00)
"""

from __future__ import annotations

import datetime as dt


def meteorological_tn_day(timestamp: dt.datetime) -> dt.date:
    """
    Journée à laquelle appartient la `tn` d'une lecture à `timestamp`.
    Reproduit `date_trunc('day', t - 18h - 1s) + 1 day`.

    Conséquence pratique : `D 18:00:00` reste dans `tn(D)`, `D 18:00:01`
    bascule dans `tn(D+1)`.
    """
    shifted = timestamp - dt.timedelta(hours=18, seconds=1)
    return shifted.date() + dt.timedelta(days=1)


def meteorological_tx_day(timestamp: dt.datetime) -> dt.date:
    """
    Journée à laquelle appartient la `tx` d'une lecture à `timestamp`.
    Reproduit `date_trunc('day', t - 6h - 1s)`.

    Conséquence pratique : `D 06:00:00` reste dans `tx(D-1)`, `D 06:00:01`
    bascule dans `tx(D)`.
    """
    shifted = timestamp - dt.timedelta(hours=6, seconds=1)
    return shifted.date()
