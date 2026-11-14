from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and r.json()["sites"] == 3


def test_sites_overview(client):
    sites = client.get("/api/sites").json()
    assert len(sites) == 3
    for s in sites:
        assert s["complete"] and s["terrain"] and s["summary"]


@pytest.mark.parametrize("kind", ["horizon", "terrain", "timeseries"])
def test_site_files(client, kind):
    for s in client.get("/api/sites").json():
        r = client.get(f"/api/sites/{s['id']}/{kind}")
        assert r.status_code == 200, r.text
        assert r.json()["site_id"] == s["id"]


def test_sanity_of_precomputed(client):
    """Comprobaciones de cordura del documento del Integrante 1."""
    for s in client.get("/api/sites").json():
        hz = client.get(f"/api/sites/{s['id']}/horizon").json()["horizon_el_deg"]
        assert len(hz) == 360 and all(-5 <= v <= 15 for v in hz)
        ts = client.get(f"/api/sites/{s['id']}/timeseries").json()
        limit = (90 - abs(s["lat"])) + 1.6
        assert all(abs(x["sun"]["el"]) <= limit for x in ts["samples"])
        times = [config.parse_utc(x["t"]) for x in ts["samples"]]
        assert all(b - a == timedelta(hours=1) for a, b in zip(times, times[1:]))
        assert 0 <= ts["summary"]["sun_visible_pct"] <= 100
    pcts = [s["summary"]["sun_visible_pct"] for s in client.get("/api/sites").json()]
    assert len(set(pcts)) == len(pcts)


def test_unknown_site_error_format(client):
    r = client.get("/api/sites/nope/horizon")
    assert r.status_code == 404
    assert r.json() == {"error": "site_not_found", "detail": "No existe site 'nope'."}


def test_profiles(client):
    ids = [p["id"] for p in client.get("/api/profiles").json()]
    assert ids == ["solar", "comms", "safety", "balanced"]


def test_score(client):
    r = client.get("/api/score", params={"profile": "comms"})
    assert r.status_code == 200
    body = r.json()
    assert body["profile"] == "comms" and len(body["ranking"]) == 3
    assert body["recommended"] == body["ranking"][0]["site_id"]


def test_score_bad_profile(client):
    r = client.get("/api/score", params={"profile": "nope"})
    assert r.status_code == 404 and r.json()["error"] == "profile_not_found"


def test_point_and_score_with_point(client):
    r = client.post("/api/point", json={"lat": -86.1, "lon": -3.2})
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["quality"] == "estimated" and p["point_id"].startswith("p-")
    assert p["elapsed_s"] < 5
    assert p["horizon"]["mode"] == "fast"
    s = client.get("/api/score", params={"profile": "solar", "point_id": p["point_id"]}).json()
    assert len(s["ranking"]) == 4
    assert s["recommended"] != p["point_id"]
    assert client.get(f"/api/sites/{p['point_id']}/timeseries").status_code == 200


def test_point_outside_dem(client):
    r = client.post("/api/point", json={"lat": -10, "lon": 0})
    assert r.status_code == 422 and r.json()["error"] == "outside_dem"


def test_point_invalid_body(client):
    r = client.post("/api/point", json={"lat": -100, "lon": 0})
    assert r.status_code == 422 and r.json()["error"] == "invalid_request"


def test_report(client):
    r = client.post("/api/report", json={"site_id": "malapert", "profile": "solar"})
    assert r.status_code == 200, r.text
    rep = r.json()
    assert rep["site"]["id"] == "malapert" and 1 <= rep["rank"] <= 3
    assert rep["limitations"] and rep["data_sources"] and len(rep["comparison"]) == 3


def test_report_uses_terrain_elevation(client):
    terrain = client.get("/api/sites/malapert/terrain").json()
    rep = client.post("/api/report", json={"site_id": "malapert", "profile": "solar"}).json()
    assert rep["site"]["elevation_m"] == terrain["elevation_m"]
