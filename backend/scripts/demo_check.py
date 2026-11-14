"""Llama a todos los endpoints de un backend en marcha y comprueba códigos y forma básica.

Uso (con el servidor arrancado):  python scripts/demo_check.py [--base http://localhost:8000/api]
"""

import argparse
import sys

import httpx

OK, FAIL = "OK  ", "FALLA"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000/api")
    base = ap.parse_args().base
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    failures = 0

    def check(label, resp, cond=lambda j: True):
        nonlocal failures
        try:
            good = resp.status_code == 200 and cond(resp.json())
        except Exception:
            good = False
        failures += not good
        print(f"[{OK if good else FAIL}] {resp.status_code} {label}")
        return resp.json() if good else None

    with httpx.Client(base_url=base, timeout=10) as c:
        try:
            h = check("GET /health", c.get("/health"), lambda j: j["status"] == "ok")
        except httpx.ConnectError:
            print(f"No se puede conectar a {base}. ¿Está arrancado uvicorn?")
            return 2
        if h and not h["kernels_loaded"]:
            print("       aviso: kernels_loaded = false (datos mock o science/ sin kernels)")

        sites = check("GET /sites", c.get("/sites"), lambda j: len(j) == 3) or []
        for s in sites:
            sid = s["id"]
            if s.get("source") == "mock":
                print(f"       aviso: {sid} usa datos MOCK")
            check(f"GET /sites/{sid}/horizon", c.get(f"/sites/{sid}/horizon"), lambda j: len(j["horizon_el_deg"]) > 0)
            check(f"GET /sites/{sid}/terrain", c.get(f"/sites/{sid}/terrain"), lambda j: "slope_deg_mean" in j)
            check(f"GET /sites/{sid}/timeseries", c.get(f"/sites/{sid}/timeseries"), lambda j: len(j["samples"]) > 0)

        profiles = check("GET /profiles", c.get("/profiles"), lambda j: len(j) >= 2) or []
        for p in profiles:
            check(f"GET /score?profile={p['id']}", c.get("/score", params={"profile": p["id"]}),
                  lambda j: j["recommended"] and j["ranking"])

        pt = check("POST /point", c.post("/point", json={"lat": -86.1, "lon": -3.2}),
                   lambda j: j["quality"] == "estimated")
        if pt:
            print(f"       punto libre en {pt['elapsed_s']} s" + ("  (¡> 5 s!)" if pt["elapsed_s"] > 5 else ""))
            check("GET /score con punto libre", c.get("/score", params={"profile": "solar", "point_id": pt["point_id"]}),
                  lambda j: j["recommended"] != pt["point_id"])
        if sites:
            check("POST /report", c.post("/report", json={"site_id": sites[0]["id"], "profile": "solar"}),
                  lambda j: j["limitations"] and j["data_sources"])

    print("\nTodo correcto." if not failures else f"\n{failures} comprobación(es) fallida(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
