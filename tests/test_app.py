import os
import pytest
import httpx

BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:8080")


def test_health_and_kpis():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

        k = client.get("/api/kpis")
        assert k.status_code == 200
        data = k.json()
        assert data["total_risks"] == 12
        assert data["dda_total"] == 93


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/login",
        "/documentos",
        "/documentos/LFB-POL-01/imprimir",
        "/procesos",
        "/activos",
        "/riesgos",
        "/dda",
        "/dda?tab=trazabilidad",
        "/dda?tab=raci",
        "/incidentes",
        "/cadena-frio",
        "/operaciones?tab=respaldos",
        "/operaciones?tab=accesos",
        "/operaciones?tab=capacitaciones",
        "/operaciones?tab=proveedores",
        "/auditoria",
        "/auditoria/revision-direccion/imprimir",
        "/portal-cliente",
        "/configuracion",
        "/docs",
        "/static/css/app.css",
        "/static/js/htmx.min.js",
    ],
)
def test_all_pages_render_without_cdn(path):
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        r = client.get(path)
        assert r.status_code == 200, f"Failed on {path}"
        if path.endswith(".html") or ("." not in path and path != "/docs"):
            assert "cdn.tailwindcss.com" not in r.text
            assert "unpkg.com" not in r.text


def test_rbac_auditor_readonly_enforcement():
    with httpx.Client(base_url=BASE_URL, timeout=10.0, follow_redirects=False) as client:
        # Switch to read-only auditor
        sw = client.post("/switch-role", data={"email": "auditor@evaluacion.ucol.mx"})
        assert sw.status_code == 303

        # Attempt write operation as auditor -> must be 403
        blocked = client.post(
            "/cadena-frio",
            data={
                "branch": "Sucursal Camino Real",
                "unit_name": "Cámara de Cortes Finos #1",
                "temp_c": "2.0",
                "min_c": "-2.0",
                "max_c": "4.0",
                "corrective_action": "Intento auditor",
            },
        )
        assert blocked.status_code == 403


def test_cold_chain_out_of_range_creates_incident_and_export_json():
    with httpx.Client(base_url=BASE_URL, timeout=10.0, follow_redirects=False) as client:
        sw = client.post("/switch-role", data={"email": "cgarcia75@ucol.mx"})
        assert sw.status_code == 303

        before = client.get("/api/kpis").json()["inc_total"]
        resp = client.post(
            "/cadena-frio",
            data={
                "branch": "Sucursal Camino Real",
                "unit_name": "Cámara de Cortes Finos #1",
                "temp_c": "7.2",
                "min_c": "-2.0",
                "max_c": "4.0",
                "corrective_action": "Prueba automática de alerta térmica",
            },
        )
        assert resp.status_code == 303
        after = client.get("/api/kpis").json()["inc_total"]
        assert after == before + 1

        exp = client.get("/api/export/expediente.json")
        assert exp.status_code == 200
        payload = exp.json()
        assert len(payload["assets"]) == 20
        assert len(payload["dda_controls"]) == 93
