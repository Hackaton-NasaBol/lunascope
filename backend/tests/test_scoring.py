import pytest

from lunascope.scoring import PROFILES, rank, score_site, subscores
from lunascope.scoring.explain import ESTIMATED_TOP_NOTE


def cand(cid, sun, earth, dark_h, slope, hazard, quality="full"):
    return {
        "id": cid, "name": cid, "quality": quality,
        "summary": {"sun_visible_pct": sun, "earth_visible_pct": earth, "both_visible_pct": 0,
                    "longest_dark_h": dark_h, "longest_no_earth_h": 0,
                    "windows": [{"start": "2027-09-03T05:00:00Z", "end": "2027-09-09T17:00:00Z", "hours": 156}]},
        "terrain": {"slope_deg_mean": slope, "hazard_pct": hazard},
    }


@pytest.mark.parametrize("pid", PROFILES)
def test_weights_sum_to_one(pid):
    assert sum(PROFILES[pid]["weights"].values()) == pytest.approx(1.0)


@pytest.mark.parametrize("pid", PROFILES)
def test_perfect_site_scores_100(pid):
    sub = subscores(cand("x", 100, 100, 0, 0, 0)["summary"], {"slope_deg_mean": 0, "hazard_pct": 0})
    assert sub == {"sun": 100, "earth": 100, "continuity": 100, "terrain": 100}
    assert score_site(sub, PROFILES[pid]["weights"]) == 100


def test_subscores_formulas():
    sub = subscores(cand("x", 71.3, 58.0, 48, 4.2, 3.5)["summary"], {"slope_deg_mean": 4.2, "hazard_pct": 3.5})
    assert sub["continuity"] == pytest.approx(100 * (1 - 48 / 720), abs=0.05)  # 93,3
    assert sub["terrain"] == pytest.approx(100 * (1 - 4.2 / 15) * (1 - 0.035), abs=0.05)
    # Fuera de rango se recorta a 0
    assert subscores(cand("x", 0, 0, 1000, 30, 0)["summary"], {"slope_deg_mean": 30, "hazard_pct": 0})["continuity"] == 0
    assert subscores(cand("x", 0, 0, 0, 30, 0)["summary"], {"slope_deg_mean": 30, "hazard_pct": 0})["terrain"] == 0


def test_estimated_never_recommended():
    cands = [cand("a", 40, 40, 100, 5, 5), cand("b", 30, 30, 150, 6, 6),
             cand("p-1", 100, 100, 0, 0, 0, quality="estimated")]
    out = rank(cands, "solar")
    assert out["ranking"][0]["site_id"] == "p-1"
    assert out["recommended"] == "a"
    assert ESTIMATED_TOP_NOTE in out["notes"]
    assert ESTIMATED_TOP_NOTE in out["ranking"][0]["explanation"]


def test_profile_changes_order():
    sunny = cand("sunny", 90, 20, 24, 5, 5)
    talky = cand("talky", 30, 95, 120, 5, 5)
    assert rank([sunny, talky], "solar")["recommended"] == "sunny"
    assert rank([sunny, talky], "comms")["recommended"] == "talky"


def test_explanations_2_to_4_sentences_with_numbers():
    out = rank([cand("a", 71.3, 58, 96, 4, 3), cand("b", 50, 70, 150, 6, 8), cand("c", 60, 40, 200, 3, 1)], "solar")
    for row in out["ranking"]:
        assert 2 <= len(row["explanation"]) <= 4
    a = next(r for r in out["ranking"] if r["site_id"] == "a")
    text = " ".join(a["explanation"])
    # "a" es el mejor de los 3 en Sol (71 %) y en noche más corta (96 h): su punto fuerte es uno de ellos.
    assert ("71 %" in text or "96 h" in text) and "el mejor de los 3 sitios" in text
    assert "3 sep 05:00 UTC, 156 h" in text


def test_ties_are_not_called_best():
    out = rank([cand("a", 50, 50, 300, 5, 5), cand("b", 60, 40, 300, 5, 5)], "solar")
    for row in out["ranking"]:
        assert not any("noche" in s and "el mejor" in s for s in row["explanation"])


def test_unknown_profile():
    with pytest.raises(KeyError):
        rank([cand("a", 1, 1, 1, 1, 1)], "nope")


def test_strong_point_is_relative_not_absolute():
    """Un 57 % de Tierra que es el peor de los 3 no puede ser el 'punto fuerte'."""
    rows = rank([cand("a", 46, 68, 300, 3, 5), cand("b", 45, 73, 300, 6, 8), cand("h", 39, 57, 300, 6.5, 9)], "comms")
    h = next(r for r in rows["ranking"] if r["site_id"] == "h")
    assert not any(s.startswith("Su punto fuerte") and "el peor" in s for s in h["explanation"])


def test_continuity_distinguishes_real_night_lengths():
    """Con noches reales de 328 h y 336 h, la continuidad no puede ser 0 para ambas."""
    a = subscores(cand("a", 50, 50, 328, 5, 5)["summary"], {"slope_deg_mean": 5, "hazard_pct": 5})
    b = subscores(cand("b", 50, 50, 336, 5, 5)["summary"], {"slope_deg_mean": 5, "hazard_pct": 5})
    assert a["continuity"] > b["continuity"] > 0
    assert subscores(cand("c", 0, 0, 1441, 0, 0)["summary"], {"slope_deg_mean": 0, "hazard_pct": 0})["continuity"] == 0
