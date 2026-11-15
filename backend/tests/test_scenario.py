"""Escenarios de fecha: series, puntuación e informe para otras fechas de misión."""

import pytest
from fastapi.testclient import TestClient

from app import config, scenario
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


live = pytest.mark.skipif(not scenario.live_available(), reason="faltan kernels SPICE: no se pueden calcular otras fechas")


def test_mission_info(client):
    m = client.get("/api/mission").json()
    assert m["default_start"] == config.fmt_utc(config.MISSION_START)
    assert m["default_days"] == config.MISSION_DAYS and m["max_days"] == scenario.MAX_DAYS
    assert isinstance(m["live_dates"], bool)


def test_default_window_is_precomputed(client):
    a = client.get("/api/sites/malapert/timeseries").json()
    b = client.get("/api/sites/malapert/timeseries",
                   params={"start": config.fmt_utc(config.MISSION_START), "days": config.MISSION_DAYS}).json()
    assert a == b and len(a["samples"]) == 1441


@live
def test_other_dates(client):
    r = client.get("/api/sites/malapert/timeseries", params={"start": "2028-03-01T00:00:00Z", "days": 30})
    assert r.status_code == 200, r.text
    ts = r.json()
    assert ts["start"] == "2028-03-01T00:00:00Z" and len(ts["samples"]) == 721 and ts["source"] == "real"
    assert ts["samples"][0]["t"] == "2028-03-01T00:00:00Z"
    long = client.get("/api/sites/malapert/timeseries", params={"start": "2028-03-01T00:00:00Z", "days": 120}).json()
    assert long["step_hours"] == 2.0 and len(long["samples"]) == 120 * 12 + 1


@live
def test_live_matches_precomputed():
    """Recalcular la ventana por defecto en vivo da lo mismo que el JSON precalculado."""
    ts = scenario._cached("malapert-check", *_malapert_args())
    pre = TestClient(app).__enter__().get("/api/sites/malapert/timeseries").json()
    assert ts["summary"] == pre["summary"]
    assert ts["samples"][100] == pre["samples"][100]


def _malapert_args():
    from app.store import store

    store.load_all()
    s, hz, t = store.sites["malapert"], store.get("malapert", "horizon"), store.get("malapert", "terrain")
    return (s["lat"], s["lon"], t["elevation_m"], tuple(hz["horizon_el_deg"]), hz["az_step_deg"],
            config.fmt_utc(config.MISSION_START), config.MISSION_DAYS, 1.0)


@live
def test_score_and_report_use_the_window(client):
    default = client.get("/api/score", params={"profile": "solar"}).json()
    other = client.get("/api/score", params={"profile": "solar", "start": "2028-03-01T00:00:00Z", "days": 30}).json()
    assert len(other["ranking"]) == len(default["ranking"])
    assert [r["breakdown"] for r in other["ranking"]] != [r["breakdown"] for r in default["ranking"]]
    rep = client.post("/api/report", json={"site_id": "malapert", "profile": "solar",
                                           "start": "2028-03-01T00:00:00Z", "days": 30}).json()
    assert rep["mission_window"] == {"start": "2028-03-01T00:00:00Z", "end": "2028-03-31T00:00:00Z", "hours": 720.0}


@pytest.mark.parametrize("params,error", [
    ({"start": "2028-03-01T00:00:00Z", "days": 0}, "invalid_days"),
    ({"start": "2028-03-01T00:00:00Z", "days": 999}, "invalid_days"),
    ({"start": "2200-01-01T00:00:00Z", "days": 10}, "date_out_of_range"),
    ({"start": "mañana", "days": 10}, "invalid_date"),
])
def test_invalid_windows(client, params, error):
    r = client.get("/api/sites/malapert/timeseries", params=params)
    assert r.status_code == 422 and r.json()["error"] == error


@live
def test_concurrent_requests_do_not_crash_spice(client):
    """CSPICE no es seguro con hilos: sin pipeline.SPICE_LOCK, esto tiraba el proceso (SPICE(BADSUBSCRIPT))."""
    from concurrent.futures import ThreadPoolExecutor

    def get(i: int):
        start = f"2029-{1 + i % 12:02d}-01T00:00:00Z"
        sid = ["malapert", "haworth", "mons_mouton_plateau"][i % 3]
        return client.get(f"/api/sites/{sid}/timeseries", params={"start": start, "days": 10}).status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(get, range(24)))
    assert codes == [200] * 24


def test_scenario_summary_default(client):
    r = client.get("/api/scenario", params={"profile": "solar"}).json()
    assert r["is_default"] and r["recommended"] in {s["site_id"] for s in r["sites"]}
    m = next(s for s in r["sites"] if s["site_id"] == "malapert")
    assert m["sun_visible_pct"] == 51.6 and m["best_window"]["hours"] == 384.0
    # El 1 sep 2027 a las 00:00 en Malapert no hay Sol (sale ~4,8 d después) y la Tierra se ve todo el periodo.
    assert m["at_landing"]["sun_visible"] is False and 100 < m["at_landing"]["sun_change_h"] < 130
    assert m["at_landing"]["earth_visible"] is True and m["at_landing"]["earth_change_h"] is None


@live
def test_scenario_summary_other_date(client):
    r = client.get("/api/scenario", params={"profile": "comms", "start": "2028-03-01T00:00:00Z", "days": 60}).json()
    assert not r["is_default"] and r["start"] == "2028-03-01T00:00:00Z" and r["profile"] == "comms"
    m = next(s for s in r["sites"] if s["site_id"] == "malapert")
    assert m["sun_visible_pct"] == 36.4 and m["score"] is not None
