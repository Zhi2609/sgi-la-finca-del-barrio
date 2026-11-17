import csv
import hashlib
import io
import json
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeSerializer

from app.config import APP_TITLE, APP_VERSION, SESSION_SECRET, TEAM_ENGINEERS
from app.db import close_pool, get_conn, init_schema_and_seed, log_audit, verify_password

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
serializer = URLSafeSerializer(SESSION_SECRET, salt="lfb-sgi-session")
COOKIE_NAME = "lfb_sgi_session"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_schema_and_seed()
    yield
    close_pool()


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Sistema de Gestión Integral (ISO/IEC 27001:2022, ISO 22000:2018, ISO/IEC 38500:2024, ITIL 4) · La Finca del Barrio",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def get_current_user(request: Request) -> dict:
    token = request.cookies.get(COOKIE_NAME)
    email = "cgarcia75@ucol.mx"
    if token:
        try:
            data = serializer.loads(token)
            email = data.get("email", email)
        except BadSignature:
            pass
    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, email, full_name, role, role_label, can_write FROM users WHERE email = %s AND active = TRUE",
            (email,),
        ).fetchone()
        if not user:
            user = conn.execute(
                "SELECT id, email, full_name, role, role_label, can_write FROM users ORDER BY id LIMIT 1"
            ).fetchone()
    return user


def require_write(user: dict) -> None:
    if not user or not user.get("can_write"):
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado (Control 5.15 / 5.18): El rol Auditor Externo tiene permisos de solo lectura.",
        )


def get_company() -> dict:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM company_settings WHERE id = 1").fetchone()


def get_all_users() -> list[dict]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, email, full_name, role, role_label, can_write FROM users WHERE active = TRUE ORDER BY id"
        ).fetchall()


def base_ctx(request: Request, active_nav: str, **extra) -> dict:
    return {
        "request": request,
        "app_title": APP_TITLE,
        "app_version": APP_VERSION,
        "active_nav": active_nav,
        "user": get_current_user(request),
        "all_users": get_all_users(),
        "company": get_company(),
        "team_engineers": TEAM_ENGINEERS,
        **extra,
    }


def compute_kpis(conn) -> dict:
    risks = conn.execute("SELECT semaphore, treatment_status FROM risks").fetchall()
    dda = conn.execute("SELECT decision, implementation_status FROM dda_controls").fetchall()
    incidents = conn.execute("SELECT severity, status FROM incidents").fetchall()
    cold = conn.execute("SELECT in_range FROM cold_chain_logs").fetchall()
    backups = conn.execute("SELECT restore_tested, restore_result FROM backups").fetchall()
    trainings = conn.execute("SELECT attendees_count, target_count FROM trainings").fetchall()
    suppliers = conn.execute("SELECT compliance_status, nda_signed FROM suppliers").fetchall()
    findings = conn.execute("SELECT finding_type, status FROM audit_findings").fetchall()

    total_risks = len(risks)
    high_risks = sum(1 for r in risks if r["semaphore"] == "Alto")
    treated_risks = sum(1 for r in risks if r["treatment_status"] == "Implementado")

    dda_applicable = [c for c in dda if c["decision"] != "No aplica"]
    dda_impl = sum(1 for c in dda_applicable if c["implementation_status"] == "Implementado")
    dda_pct = round((dda_impl / len(dda_applicable)) * 100) if dda_applicable else 0

    open_inc = sum(1 for i in incidents if i["status"] not in ("Resuelto", "Cerrado"))
    crit_open = sum(1 for i in incidents if i["severity"] == "Crítica" and i["status"] not in ("Resuelto", "Cerrado"))

    cold_total = len(cold)
    cold_ok = sum(1 for c in cold if c["in_range"])
    cold_pct = round((cold_ok / cold_total) * 100) if cold_total else 100

    tested_bkp = [b for b in backups if b["restore_tested"]]
    ok_bkp = sum(1 for b in tested_bkp if b["restore_result"] == "Exitosa")
    bkp_pct = round((ok_bkp / len(tested_bkp)) * 100) if tested_bkp else 0

    att = sum(t["attendees_count"] for t in trainings)
    tgt = sum(t["target_count"] for t in trainings)
    train_pct = round((att / tgt) * 100) if tgt else 0

    sup_sla_pct = round((sum(1 for s in suppliers if s["nda_signed"]) / len(suppliers)) * 100) if suppliers else 0
    open_findings = sum(1 for f in findings if f["status"] != "Cerrada")

    return {
        "total_risks": total_risks,
        "high_risks": high_risks,
        "treated_risks": treated_risks,
        "dda_total": len(dda),
        "dda_applicable": len(dda_applicable),
        "dda_impl": dda_impl,
        "dda_pct": dda_pct,
        "inc_total": len(incidents),
        "inc_open": open_inc,
        "crit_open": crit_open,
        "cold_total": cold_total,
        "cold_ok": cold_ok,
        "cold_pct": cold_pct,
        "bkp_total": len(backups),
        "bkp_pct": bkp_pct,
        "train_pct": train_pct,
        "sup_sla_pct": sup_sla_pct,
        "open_findings": open_findings,
        "pos_availability": "99.4%" if crit_open == 0 else "98.2%",
    }


# ---------------------------------------------------------------------------
# Health & Auth
# ---------------------------------------------------------------------------
@app.get("/api/health", tags=["Sistema"])
def api_health():
    with get_conn() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "database": "postgresql", "app": APP_TITLE, "version": APP_VERSION}


@app.get("/api/kpis", tags=["Sistema"])
def api_kpis():
    with get_conn() as conn:
        return compute_kpis(conn)


@app.get("/api/export/expediente.json", tags=["Sistema"])
def api_export_expediente(request: Request):
    user = get_current_user(request)
    with get_conn() as conn:
        payload = {
            "exported_at": datetime.now().isoformat(),
            "exported_by": user["email"],
            "company": conn.execute("SELECT * FROM company_settings WHERE id = 1").fetchone(),
            "processes": conn.execute("SELECT * FROM processes ORDER BY code").fetchall(),
            "assets": conn.execute("SELECT * FROM assets ORDER BY code").fetchall(),
            "risks": conn.execute("SELECT * FROM risks ORDER BY risk_num").fetchall(),
            "dda_controls": conn.execute("SELECT * FROM dda_controls ORDER BY id").fetchall(),
            "documents": conn.execute(
                "SELECT code, folio, title, category, norms, version, status, elaborated_by, reviewed_by, approved_by, elaborated_date, approved_date FROM documents ORDER BY id"
            ).fetchall(),
            "incidents": conn.execute("SELECT * FROM incidents ORDER BY id DESC").fetchall(),
            "cold_chain_logs": conn.execute("SELECT * FROM cold_chain_logs ORDER BY id DESC").fetchall(),
            "backups": conn.execute("SELECT * FROM backups ORDER BY id DESC").fetchall(),
            "audit_findings": conn.execute("SELECT * FROM audit_findings ORDER BY id").fetchall(),
        }
    return JSONResponse(content=json.loads(json.dumps(payload, default=str)))


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", base_ctx(request, "login"))


@app.post("/login")
def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = %s AND active = TRUE", (email.strip(),)
        ).fetchone()
        if not user or not verify_password(password, user["password_hash"]):
            return templates.TemplateResponse(
                "login.html",
                base_ctx(request, "login", error="Credenciales inválidas. Contraseña demo: FincaSGI2026!"),
                status_code=401,
            )
        log_audit(conn, user, "LOGIN", "Sesión", f"Inicio de sesión por formulario ({user['role']})")
        conn.commit()
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(COOKIE_NAME, serializer.dumps({"email": user["email"]}), httponly=True, samesite="lax")
    return resp


@app.post("/switch-role")
def switch_role(request: Request, email: str = Form(...)):
    referer = request.headers.get("referer") or "/"
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = %s AND active = TRUE", (email.strip(),)
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        log_audit(conn, user, "CAMBIO_ROL", "Sesión", f"Cambio de rol activo a {user['role_label']}")
        conn.commit()
    resp = RedirectResponse(url=referer, status_code=303)
    resp.set_cookie(COOKIE_NAME, serializer.dumps({"email": user["email"]}), httponly=True, samesite="lax")
    return resp


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    with get_conn() as conn:
        kpis = compute_kpis(conn)
        risks = conn.execute("SELECT * FROM risks ORDER BY level DESC, risk_num ASC").fetchall()
        recent_incidents = conn.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT 4").fetchall()
        recent_cold = conn.execute("SELECT * FROM cold_chain_logs ORDER BY id DESC LIMIT 4").fetchall()
        recent_audit = conn.execute("SELECT * FROM audit_trail ORDER BY id DESC LIMIT 6").fetchall()

    # Build 5x5 heatmap cells keyed by (impact, probability)
    heatmap: dict[tuple[int, int], list[dict]] = {}
    for r in risks:
        heatmap.setdefault((r["impact"], r["probability"]), []).append(r)

    return templates.TemplateResponse(
        "dashboard.html",
        base_ctx(
            request,
            "dashboard",
            kpis=kpis,
            risks=risks,
            heatmap=heatmap,
            recent_incidents=recent_incidents,
            recent_cold=recent_cold,
            recent_audit=recent_audit,
        ),
    )


# ---------------------------------------------------------------------------
# Control Documental (Cl. 7.5)
# ---------------------------------------------------------------------------
@app.get("/documentos", response_class=HTMLResponse)
def documentos_page(request: Request, category: str = ""):
    with get_conn() as conn:
        if category:
            docs = conn.execute(
                "SELECT * FROM documents WHERE category = %s ORDER BY folio", (category,)
            ).fetchall()
        else:
            docs = conn.execute("SELECT * FROM documents ORDER BY folio").fetchall()
        categories = [
            r["category"]
            for r in conn.execute("SELECT DISTINCT category FROM documents ORDER BY category").fetchall()
        ]
    return templates.TemplateResponse(
        "documentos.html",
        base_ctx(request, "documentos", docs=docs, categories=categories, selected_cat=category),
    )


@app.post("/documentos", response_class=HTMLResponse)
def create_document(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    category: str = Form(...),
    norms: str = Form(...),
    version: str = Form("v1.0"),
    summary: str = Form(...),
    body_text: str = Form(...),
):
    user = get_current_user(request)
    require_write(user)
    today = datetime.now().strftime("%d/%m/%Y")
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()["c"] + 1
        folio = f"LFB.6.{count}/GTI/{count:03d}/2026"
        html = f'<section class="mb-4"><h3 class="text-base font-bold text-vino-800 border-b border-crema-200 pb-1 mb-2">Contenido Oficial</h3><p class="text-sm text-stone-700 whitespace-pre-line">{body_text}</p></section>'
        conn.execute(
            """
            INSERT INTO documents (
                code, folio, title, category, norms, version, status,
                elaborated_by, reviewed_by, approved_by, elaborated_date, approved_date,
                summary, content_html
            ) VALUES (%s, %s, %s, %s, %s, %s, 'En revisión', %s, 'Ángel Guerrero (Owner)', 'Ramón del Toro (Dirección)', %s, 'Pendiente', %s, %s)
            """,
            (code.strip().upper(), folio, title.strip(), category, norms.strip(), version.strip(), user["full_name"], today, summary.strip(), html),
        )
        log_audit(conn, user, "CREAR_DOC", code.strip().upper(), f"Documento creado: {title}")
        conn.commit()
    return RedirectResponse(url="/documentos", status_code=303)


@app.post("/documentos/{code}/aprobar")
def approve_document(request: Request, code: str):
    user = get_current_user(request)
    require_write(user)
    today = datetime.now().strftime("%d/%m/%Y")
    with get_conn() as conn:
        conn.execute(
            "UPDATE documents SET status = 'Aprobado', approved_date = %s, approved_by = %s WHERE code = %s",
            (today, user["full_name"], code),
        )
        log_audit(conn, user, "APROBAR_DOC", code, f"Aprobación oficial registrada por {user['full_name']}")
        conn.commit()
    return RedirectResponse(url="/documentos", status_code=303)


@app.get("/documentos/{code}/imprimir", response_class=HTMLResponse)
def print_document(request: Request, code: str):
    with get_conn() as conn:
        doc = conn.execute("SELECT * FROM documents WHERE code = %s", (code,)).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
    return templates.TemplateResponse(
        "documento_print.html",
        base_ctx(request, "documentos", doc=doc),
    )


# ---------------------------------------------------------------------------
# Procesos y Cédulas (LFB-CP-01..04)
# ---------------------------------------------------------------------------
@app.get("/procesos", response_class=HTMLResponse)
def procesos_page(request: Request):
    with get_conn() as conn:
        procs = conn.execute("SELECT * FROM processes ORDER BY code").fetchall()
    return templates.TemplateResponse("procesos.html", base_ctx(request, "procesos", procs=procs))


# ---------------------------------------------------------------------------
# Activos (ACT-01..ACT-20)
# ---------------------------------------------------------------------------
@app.get("/activos", response_class=HTMLResponse)
def activos_page(request: Request, category: str = "", classification: str = "", q: str = ""):
    with get_conn() as conn:
        query = "SELECT * FROM assets WHERE 1=1"
        params: list = []
        if category:
            query += " AND category = %s"
            params.append(category)
        if classification:
            query += " AND classification = %s"
            params.append(classification)
        if q:
            query += " AND (LOWER(code) LIKE %s OR LOWER(name) LIKE %s OR LOWER(owner_role) LIKE %s)"
            like = f"%{q.lower()}%"
            params.extend([like, like, like])
        query += " ORDER BY code"
        assets = conn.execute(query, params).fetchall()
        categories = [
            r["category"] for r in conn.execute("SELECT DISTINCT category FROM assets ORDER BY category").fetchall()
        ]
    ctx = base_ctx(
        request,
        "activos",
        assets=assets,
        categories=categories,
        selected_cat=category,
        selected_cls=classification,
        q=q,
    )
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse("partials/activos_table.html", ctx)
    return templates.TemplateResponse("activos.html", ctx)


@app.post("/activos")
def create_asset(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    related_process: str = Form(...),
    owner_role: str = Form(...),
    classification: str = Form(...),
    cid_c: str = Form(...),
    cid_i: str = Form(...),
    cid_d: str = Form(...),
    protection_level: str = Form(...),
    location: str = Form(...),
):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO assets (
                code, name, category, related_process, owner_role, classification,
                cid_c, cid_i, cid_d, protection_level, location
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                code.strip().upper(), name.strip(), category, related_process.strip(),
                owner_role.strip(), classification, cid_c, cid_i, cid_d,
                protection_level.strip(), location.strip(),
            ),
        )
        log_audit(conn, user, "ALTA_ACTIVO", code.strip().upper(), f"Activo registrado: {name}")
        conn.commit()
    return RedirectResponse(url="/activos", status_code=303)


@app.get("/activos/export.csv")
def export_assets_csv():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM assets ORDER BY code").fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Código", "Activo", "Categoría", "Proceso", "Propietario", "Clasificación", "C", "I", "D", "Protección", "Ubicación", "Estado"])
    for r in rows:
        writer.writerow([
            r["code"], r["name"], r["category"], r["related_process"], r["owner_role"],
            r["classification"], r["cid_c"], r["cid_i"], r["cid_d"], r["protection_level"],
            r["location"], r["status"],
        ])
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=LFB_Inventario_Activos.csv"},
    )


# ---------------------------------------------------------------------------
# Riesgos (LFB-MCGR-01 + Plan de Tratamiento)
# ---------------------------------------------------------------------------
@app.get("/riesgos", response_class=HTMLResponse)
def riesgos_page(request: Request):
    with get_conn() as conn:
        risks = conn.execute("SELECT * FROM risks ORDER BY level DESC, risk_num ASC").fetchall()
    heatmap: dict[tuple[int, int], list[dict]] = {}
    for r in risks:
        heatmap.setdefault((r["impact"], r["probability"]), []).append(r)
    return templates.TemplateResponse(
        "riesgos.html", base_ctx(request, "riesgos", risks=risks, heatmap=heatmap)
    )


@app.post("/riesgos/{risk_num}/tratamiento", response_class=HTMLResponse)
def update_risk_treatment(
    request: Request,
    risk_num: int,
    treatment_status: str = Form(...),
    treatment_responsible: str = Form(...),
    treatment_deadline: str = Form(...),
):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE risks
            SET treatment_status = %s, treatment_responsible = %s, treatment_deadline = %s
            WHERE risk_num = %s
            """,
            (treatment_status, treatment_responsible.strip(), treatment_deadline.strip(), risk_num),
        )
        log_audit(conn, user, "ACTUALIZAR_RIESGO", f"Riesgo #{risk_num}", f"Estado tratamiento -> {treatment_status}")
        conn.commit()
    return RedirectResponse(url="/riesgos", status_code=303)


# ---------------------------------------------------------------------------
# DdA (93 controles Anexo A) + Trazabilidad + RACI
# ---------------------------------------------------------------------------
@app.get("/dda", response_class=HTMLResponse)
def dda_page(request: Request, domain: str = "", decision: str = "", tab: str = "dda"):
    with get_conn() as conn:
        query = "SELECT * FROM dda_controls WHERE 1=1"
        params: list = []
        if domain:
            query += " AND domain = %s"
            params.append(domain)
        if decision:
            query += " AND decision = %s"
            params.append(decision)
        query += " ORDER BY id"
        controls = conn.execute(query, params).fetchall()
        all_dda = conn.execute("SELECT decision, implementation_status FROM dda_controls").fetchall()
        trace = conn.execute(
            """
            SELECT t.*, r.title AS risk_title, r.level, r.semaphore, r.owner_role
            FROM traceability t
            JOIN risks r ON r.risk_num = t.risk_id
            ORDER BY t.risk_id
            """
        ).fetchall()

    summary = {
        "total": len(all_dda),
        "aplica": sum(1 for c in all_dda if c["decision"] == "Aplica"),
        "parcial": sum(1 for c in all_dda if c["decision"] == "Aplica parcialmente"),
        "no_aplica": sum(1 for c in all_dda if c["decision"] == "No aplica"),
        "impl": sum(1 for c in all_dda if c["implementation_status"] == "Implementado"),
    }
    ctx = base_ctx(
        request,
        "dda",
        controls=controls,
        trace=trace,
        summary=summary,
        selected_domain=domain,
        selected_decision=decision,
        tab=tab,
    )
    if request.headers.get("HX-Request") == "true" and tab == "dda":
        return templates.TemplateResponse("partials/dda_table.html", ctx)
    return templates.TemplateResponse("dda.html", ctx)


@app.post("/dda/{code}/estado")
def update_dda_status(
    request: Request,
    code: str,
    implementation_status: str = Form(...),
    evidence_ref: str = Form(""),
):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute(
            "UPDATE dda_controls SET implementation_status = %s, evidence_ref = %s WHERE code = %s",
            (implementation_status, evidence_ref.strip(), code),
        )
        log_audit(conn, user, "ACTUALIZAR_DDA", f"Control {code}", f"Estado -> {implementation_status}")
        conn.commit()
    return RedirectResponse(url="/dda", status_code=303)


# ---------------------------------------------------------------------------
# Incidentes ITIL 4 (FR-TI-01)
# ---------------------------------------------------------------------------
@app.get("/incidentes", response_class=HTMLResponse)
def incidentes_page(request: Request, status: str = ""):
    with get_conn() as conn:
        if status:
            rows = conn.execute("SELECT * FROM incidents WHERE status = %s ORDER BY id DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM incidents ORDER BY id DESC").fetchall()
        assets = conn.execute("SELECT code, name FROM assets ORDER BY code").fetchall()
    return templates.TemplateResponse(
        "incidentes.html",
        base_ctx(request, "incidentes", incidents=rows, assets=assets, selected_status=status),
    )


@app.post("/incidentes")
def create_incident(
    request: Request,
    branch: str = Form(...),
    asset_code: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    severity: str = Form(...),
    assigned_to: str = Form(...),
):
    user = get_current_user(request)
    require_write(user)
    sla = 2 if severity in ("Crítica", "Alta") else 24
    with get_conn() as conn:
        next_num = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM incidents").fetchone()["n"]
        folio = f"INC-2026-{next_num:03d}"
        conn.execute(
            """
            INSERT INTO incidents (
                folio, branch, asset_code, title, description, severity, sla_hours,
                status, reported_by, assigned_to
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Abierto', %s, %s)
            """,
            (folio, branch, asset_code, title.strip(), description.strip(), severity, sla, user["full_name"], assigned_to.strip()),
        )
        log_audit(conn, user, "NUEVO_INCIDENTE", folio, f"{severity} en {branch}: {title}")
        conn.commit()
    return RedirectResponse(url="/incidentes", status_code=303)


@app.post("/incidentes/{folio}/estado")
def update_incident_status(
    request: Request,
    folio: str,
    status: str = Form(...),
    resolution_notes: str = Form(""),
    lesson_learned: str = Form(""),
):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE incidents
            SET status = %s,
                resolution_notes = CASE WHEN %s <> '' THEN %s ELSE resolution_notes END,
                lesson_learned = CASE WHEN %s <> '' THEN %s ELSE lesson_learned END,
                resolved_at = CASE WHEN %s IN ('Resuelto', 'Cerrado') THEN COALESCE(resolved_at, NOW()) ELSE NULL END
            WHERE folio = %s
            """,
            (status, resolution_notes.strip(), resolution_notes.strip(), lesson_learned.strip(), lesson_learned.strip(), status, folio),
        )
        log_audit(conn, user, "ACTUALIZAR_INCIDENTE", folio, f"Estado -> {status}")
        conn.commit()
    return RedirectResponse(url="/incidentes", status_code=303)


# ---------------------------------------------------------------------------
# Cadena de Frío (FR-CA-02 · ISO 22000 + ISO 27001 8.16)
# ---------------------------------------------------------------------------
@app.get("/cadena-frio", response_class=HTMLResponse)
def cadena_frio_page(request: Request):
    with get_conn() as conn:
        logs = conn.execute("SELECT * FROM cold_chain_logs ORDER BY id DESC").fetchall()
    return templates.TemplateResponse("cadena_frio.html", base_ctx(request, "cadena_frio", logs=logs))


@app.post("/cadena-frio")
def create_cold_log(
    request: Request,
    branch: str = Form(...),
    unit_name: str = Form(...),
    temp_c: float = Form(...),
    min_c: float = Form(-2.0),
    max_c: float = Form(4.0),
    corrective_action: str = Form(""),
):
    user = get_current_user(request)
    require_write(user)
    in_range = min_c <= temp_c <= max_c
    action_text = corrective_action.strip() or (
        "Operación nominal dentro de rango" if in_range else "ALERTA: Revisión inmediata de equipo y resguardo de lote."
    )
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO cold_chain_logs (branch, unit_name, temp_c, min_c, max_c, in_range, corrective_action, recorded_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (branch, unit_name, temp_c, min_c, max_c, in_range, action_text, user["full_name"]),
        )
        if not in_range:
            next_num = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM incidents").fetchone()["n"]
            folio = f"INC-2026-{next_num:03d}"
            conn.execute(
                """
                INSERT INTO incidents (
                    folio, branch, asset_code, title, description, severity, sla_hours,
                    status, reported_by, assigned_to
                ) VALUES (%s, %s, 'ACT-06', %s, %s, 'Crítica', 2, 'Abierto', %s, 'Encargado de compras / TI')
                """,
                (
                    folio,
                    branch,
                    f"Alerta Cadena de Frío en {unit_name} ({temp_c} °C)",
                    f"Lectura fuera de rango [{min_c} °C, {max_c} °C]. Acción inicial: {action_text}",
                    user["full_name"],
                ),
            )
            log_audit(conn, user, "ALERTA_FRIO", unit_name, f"Fuera de rango ({temp_c} °C) en {branch}. Ticket {folio} generado.")
        else:
            log_audit(conn, user, "REGISTRO_FRIO", unit_name, f"Lectura {temp_c} °C en {branch} (En rango)")
        conn.commit()
    return RedirectResponse(url="/cadena-frio", status_code=303)


# ---------------------------------------------------------------------------
# Operaciones: Respaldos (FR-TI-02), Accesos (FR-TI-03), Capacitación (FR-SI-02), Proveedores (FR-CA-01)
# ---------------------------------------------------------------------------
@app.get("/operaciones", response_class=HTMLResponse)
def operaciones_page(request: Request, tab: str = "respaldos"):
    with get_conn() as conn:
        backups = conn.execute("SELECT * FROM backups ORDER BY id DESC").fetchall()
        access_rows = conn.execute("SELECT * FROM access_reviews ORDER BY id DESC").fetchall()
        trainings = conn.execute("SELECT * FROM trainings ORDER BY id DESC").fetchall()
        suppliers = conn.execute("SELECT * FROM suppliers ORDER BY id").fetchall()
    return templates.TemplateResponse(
        "operaciones.html",
        base_ctx(
            request,
            "operaciones",
            tab=tab,
            backups=backups,
            access_rows=access_rows,
            trainings=trainings,
            suppliers=suppliers,
        ),
    )


@app.post("/operaciones/respaldos")
def create_backup(
    request: Request,
    backup_date: str = Form(...),
    scope: str = Form(...),
    destination: str = Form(...),
    restore_tested: bool = Form(False),
    restore_result: str = Form("No probada"),
    notes: str = Form(""),
):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO backups (backup_date, scope, destination, restore_tested, restore_result, responsible, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (backup_date, scope.strip(), destination, restore_tested, restore_result, user["full_name"], notes.strip()),
        )
        log_audit(conn, user, "REGISTRO_RESPALDO", "FR-TI-02", f"{destination}: {scope} ({restore_result})")
        conn.commit()
    return RedirectResponse(url="/operaciones?tab=respaldos", status_code=303)


@app.post("/operaciones/accesos")
def create_access_review(
    request: Request,
    employee_name: str = Form(...),
    role_area: str = Form(...),
    branch: str = Form(...),
    system_name: str = Form(...),
    action_type: str = Form(...),
    action_date: str = Form(...),
):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO access_reviews (employee_name, role_area, branch, system_name, action_type, action_date, verified_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Completado')
            """,
            (employee_name.strip(), role_area.strip(), branch, system_name.strip(), action_type, action_date, user["full_name"]),
        )
        log_audit(conn, user, "CONTROL_ACCESO", "FR-TI-03", f"{action_type} para {employee_name} ({system_name})")
        conn.commit()
    return RedirectResponse(url="/operaciones?tab=accesos", status_code=303)


@app.post("/operaciones/capacitaciones")
def create_training(
    request: Request,
    topic: str = Form(...),
    norm_ref: str = Form(...),
    session_date: str = Form(...),
    attendees_count: int = Form(...),
    target_count: int = Form(...),
    branch: str = Form(...),
    evidence_note: str = Form(""),
):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO trainings (topic, norm_ref, session_date, facilitator, attendees_count, target_count, branch, evidence_note)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (topic.strip(), norm_ref.strip(), session_date, user["full_name"], attendees_count, target_count, branch, evidence_note.strip()),
        )
        log_audit(conn, user, "CAPACITACION", "FR-SI-02", f"{topic} ({attendees_count}/{target_count})")
        conn.commit()
    return RedirectResponse(url="/operaciones?tab=capacitaciones", status_code=303)


@app.post("/operaciones/proveedores")
def create_supplier(
    request: Request,
    name: str = Form(...),
    service_type: str = Form(...),
    sla_target: str = Form(...),
    nda_signed: bool = Form(False),
    last_eval_date: str = Form(...),
    compliance_status: str = Form(...),
    notes: str = Form(""),
):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO suppliers (name, service_type, sla_target, nda_signed, last_eval_date, compliance_status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (name.strip(), service_type.strip(), sla_target.strip(), nda_signed, last_eval_date, compliance_status, notes.strip()),
        )
        log_audit(conn, user, "EVAL_PROVEEDOR", "FR-CA-01", f"{name} -> {compliance_status}")
        conn.commit()
    return RedirectResponse(url="/operaciones?tab=proveedores", status_code=303)


# ---------------------------------------------------------------------------
# Auditoría Interna, No Conformidades (Cl. 9 y 10) & Bitácora del Sistema
# ---------------------------------------------------------------------------
@app.get("/auditoria", response_class=HTMLResponse)
def auditoria_page(request: Request):
    with get_conn() as conn:
        findings = conn.execute("SELECT * FROM audit_findings ORDER BY id DESC").fetchall()
        logs = conn.execute("SELECT * FROM audit_trail ORDER BY id DESC LIMIT 40").fetchall()
    return templates.TemplateResponse(
        "auditoria.html", base_ctx(request, "auditoria", findings=findings, trail=logs)
    )


@app.post("/auditoria/hallazgos")
def create_finding(
    request: Request,
    norm_clause: str = Form(...),
    area_process: str = Form(...),
    finding_type: str = Form(...),
    description: str = Form(...),
    root_cause: str = Form(""),
    corrective_action: str = Form(""),
    responsible: str = Form(...),
    due_date: str = Form(...),
):
    user = get_current_user(request)
    require_write(user)
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        n = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM audit_findings").fetchone()["n"]
        code = f"AUD-2026-{n:02d}"
        status = "Cerrada" if finding_type == "Conforme" else "Abierta"
        conn.execute(
            """
            INSERT INTO audit_findings (
                code, norm_clause, area_process, finding_type, description,
                root_cause, corrective_action, responsible, due_date, status, audit_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                code, norm_clause.strip(), area_process.strip(), finding_type,
                description.strip(), root_cause.strip(), corrective_action.strip(),
                responsible.strip(), due_date, status, today,
            ),
        )
        log_audit(conn, user, "HALLAZGO_AUDITORIA", code, f"{finding_type} en {area_process}")
        conn.commit()
    return RedirectResponse(url="/auditoria", status_code=303)


@app.post("/auditoria/hallazgos/{code}/cerrar")
def close_finding(request: Request, code: str):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute("UPDATE audit_findings SET status = 'Cerrada' WHERE code = %s", (code,))
        log_audit(conn, user, "CERRAR_HALLAZGO", code, "Acción correctiva verificada y cerrada")
        conn.commit()
    return RedirectResponse(url="/auditoria", status_code=303)


@app.get("/auditoria/revision-direccion/imprimir", response_class=HTMLResponse)
def print_management_review(request: Request):
    with get_conn() as conn:
        kpis = compute_kpis(conn)
        findings = conn.execute("SELECT * FROM audit_findings ORDER BY id").fetchall()
        high_risks = conn.execute("SELECT * FROM risks WHERE semaphore = 'Alto' ORDER BY risk_num").fetchall()
    return templates.TemplateResponse(
        "revision_direccion_print.html",
        base_ctx(request, "auditoria", kpis=kpis, findings=findings, high_risks=high_risks),
    )


# ---------------------------------------------------------------------------
# Portal Cliente (Mejora a lafincadelbarriocol.com: CFDI NOM-151 + LFPDPPP + Sello 22000)
# ---------------------------------------------------------------------------
@app.get("/portal-cliente", response_class=HTMLResponse)
def portal_cliente_page(request: Request):
    with get_conn() as conn:
        requests_list = conn.execute("SELECT * FROM cfdi_requests ORDER BY id DESC").fetchall()
    return templates.TemplateResponse(
        "portal_cliente.html", base_ctx(request, "portal_cliente", cfdi_list=requests_list)
    )


@app.post("/portal-cliente/cfdi")
def submit_cfdi_request(
    request: Request,
    ticket_folio: str = Form(...),
    branch: str = Form(...),
    rfc: str = Form(...),
    razon_social: str = Form(...),
    email: str = Form(...),
    total_mxn: float = Form(...),
):
    user = get_current_user(request)
    require_write(user)
    raw = f"{ticket_folio}|{rfc.upper()}|{total_mxn}|{datetime.now().isoformat()}"
    nom_hash = "NOM151-SHA256-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12].upper()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO cfdi_requests (ticket_folio, branch, rfc, razon_social, email, total_mxn, nom151_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (ticket_folio.strip().upper(), branch, rfc.strip().upper(), razon_social.strip(), email.strip(), total_mxn, nom_hash),
        )
        log_audit(conn, user, "TIMBRADO_CFDI_DEMO", ticket_folio.strip().upper(), f"Constancia {nom_hash}")
        conn.commit()
    return RedirectResponse(url="/portal-cliente", status_code=303)


# ---------------------------------------------------------------------------
# Configuración de Empresa y Portada
# ---------------------------------------------------------------------------
@app.get("/configuracion", response_class=HTMLResponse)
def config_page(request: Request):
    return templates.TemplateResponse("config.html", base_ctx(request, "config"))


@app.post("/configuracion")
def update_config(
    request: Request,
    name: str = Form(...),
    slogan: str = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    website: str = Form(...),
    branches: str = Form(...),
    employees_count: int = Form(...),
    owner_name: str = Form(...),
):
    user = get_current_user(request)
    require_write(user)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE company_settings
            SET name=%s, slogan=%s, address=%s, phone=%s, email=%s, website=%s,
                branches=%s, employees_count=%s, owner_name=%s, updated_at=NOW()
            WHERE id = 1
            """,
            (name.strip(), slogan.strip(), address.strip(), phone.strip(), email.strip(), website.strip(), branches.strip(), employees_count, owner_name.strip()),
        )
        log_audit(conn, user, "ACTUALIZAR_EMPRESA", "company_settings", "Datos institucionales actualizados")
        conn.commit()
    return RedirectResponse(url="/configuracion", status_code=303)
