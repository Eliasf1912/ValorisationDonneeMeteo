from __future__ import annotations

import datetime as dt

import pytest

from weather.data_sources.timescale import HybridRecordsGraphDataSource
from weather.services.records_graph.types import RecordsGraphRequest
from weather.tests.helpers.horaire import insert_mv_quotidienne_realtime
from weather.tests.helpers.records import insert_mv_record, set_cutoff
from weather.tests.helpers.stations import insert_station


def _req(**kwargs) -> RecordsGraphRequest:
    defaults = {
        "date_start": dt.date(1990, 1, 1),
        "date_end": dt.date(2027, 12, 31),
        "granularity": "year",
        "period_type": "all_time",
        "type_records": "hot",
        "month": None,
        "season": None,
        "territoire": "france",
        "territoire_id": None,
    }
    defaults.update(kwargs)
    return RecordsGraphRequest(**defaults)


@pytest.mark.django_db
def test_new_temperature_in_realtime_pipeline_appears_as_new_record():
    """
    Scénario réaliste : un record historique existe dans mv_records_battus.
    Une nouvelle température (qui bat le record) arrive via le pipeline
    temps-réel et est propagée dans mv_quotidienne_realtime par le job de
    refresh, ce que v_quotidienne expose. Le hybride doit détecter ce
    nouveau record au prochain appel.

    En test, mv_quotidienne_realtime est une vraie table (pas une MV) :
    on simule donc directement l'état post-refresh en insérant la ligne
    agrégée qui serait produite par le job de rafraîchissement en prod.
    """
    code = "75114001"
    insert_station(code, "Station Realtime", departement=75)

    historical_date = dt.date(2003, 7, 15)
    insert_mv_record(
        station_code=code,
        station_name="Station Realtime",
        period_type="all_time",
        period_value=None,
        record_type="TX",
        value=38.0,
        date=historical_date,
        department=75,
    )
    set_cutoff(dt.date(2025, 12, 31))

    ds = HybridRecordsGraphDataSource()
    request = _req()

    first = ds.fetch_graph(request)
    first_for_station = [r for r in first.records if r.station_id.strip() == code]
    assert [(r.date, r.valeur) for r in first_for_station] == [(historical_date, 38.0)]

    new_date = dt.date(2026, 7, 15)
    new_value = 45.0
    insert_mv_quotidienne_realtime(code, new_date, tn=20.0, tx=new_value)

    second = ds.fetch_graph(request)
    second_for_station = [r for r in second.records if r.station_id.strip() == code]
    values = {(r.date, r.valeur) for r in second_for_station}
    assert (historical_date, 38.0) in values
    assert (new_date, new_value) in values

    bucket_2026 = next(b for b in second.buckets if b.bucket == "2026")
    assert bucket_2026.nb_records_battus == 1


@pytest.mark.django_db
def test_record_on_cutoff_date_is_detected():
    """Quand un nouveau record tombe le MÊME jour que la cutoff_date,
    il doit être détecté (la borne de la query post-cutoff inclut la cutoff)."""
    code = "75114004"
    insert_station(code, "Station Cutoff Day", departement=75)
    insert_mv_record(
        station_code=code,
        station_name="Station Cutoff Day",
        period_type="all_time",
        period_value=None,
        record_type="TX",
        value=38.0,
        date=dt.date(2003, 7, 15),
        department=75,
    )
    cutoff = dt.date(2026, 5, 23)
    set_cutoff(cutoff)
    insert_mv_quotidienne_realtime(code, cutoff, tn=5.0, tx=45.0)

    ds = HybridRecordsGraphDataSource()
    result = ds.fetch_graph(
        _req(
            date_start=dt.date(1990, 1, 1),
            date_end=dt.date(2027, 12, 31),
        )
    )

    for_station = [r for r in result.records if r.station_id.strip() == code]
    values = {(r.date, r.valeur) for r in for_station}
    assert (cutoff, 45.0) in values, (
        f"Le record du jour de cutoff ({cutoff}) manque dans la réponse : "
        f"{for_station}"
    )


@pytest.mark.django_db
def test_record_present_in_mv_and_realtime_is_not_counted_twice():
    """Un record présent à la fois dans mv_records_battus ET dans
    mv_quotidienne_realtime (avec la même valeur) ne doit pas apparaître
    deux fois — la comparaison au seed empêche la détection redondante."""
    code = "75114005"
    insert_station(code, "Station No Dup", departement=75)

    same_day = dt.date(2026, 7, 15)
    insert_mv_record(
        station_code=code,
        station_name="Station No Dup",
        period_type="all_time",
        period_value=None,
        record_type="TX",
        value=42.0,
        date=same_day,
        department=75,
    )
    set_cutoff(dt.date(2025, 12, 31))
    insert_mv_quotidienne_realtime(code, same_day, tn=5.0, tx=42.0)

    ds = HybridRecordsGraphDataSource()
    result = ds.fetch_graph(_req())

    for_station = [r for r in result.records if r.station_id.strip() == code]
    on_same_day = [r for r in for_station if r.date == same_day]
    assert (
        len(on_same_day) == 1
    ), f"Le record du {same_day} apparaît {len(on_same_day)} fois : {on_same_day}"
    assert on_same_day[0].valeur == 42.0


@pytest.mark.django_db
def test_stale_mv_record_does_not_duplicate_with_fresher_realtime():
    """Quand le mv_records_battus a une valeur figée (par ex. 38) mais que la
    pipeline temps-réel a vu plus chaud le même jour (45), la réponse ne doit
    contenir qu'une seule ligne pour ce jour (la plus à jour)."""
    code = "75114006"
    insert_station(code, "Station Stale MV", departement=75)

    same_day = dt.date(2026, 7, 15)
    # MV avec la valeur stale (38)
    insert_mv_record(
        station_code=code,
        station_name="Station Stale MV",
        period_type="all_time",
        period_value=None,
        record_type="TX",
        value=38.0,
        date=same_day,
        department=75,
    )
    set_cutoff(dt.date(2025, 12, 31))
    # Realtime avec la valeur fraîche (45)
    insert_mv_quotidienne_realtime(code, same_day, tn=5.0, tx=45.0)

    ds = HybridRecordsGraphDataSource()
    result = ds.fetch_graph(_req())

    for_station = [r for r in result.records if r.station_id.strip() == code]
    on_same_day = [r for r in for_station if r.date == same_day]
    assert (
        len(on_same_day) == 1
    ), f"Le record du {same_day} apparaît {len(on_same_day)} fois : {on_same_day}"
    # La valeur conservée est la plus haute (post-cutoff fraîche)
    assert on_same_day[0].valeur == 45.0
