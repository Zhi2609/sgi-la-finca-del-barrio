import hashlib
import hmac
import os
import time
from contextlib import contextmanager
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import DATABASE_URL

_pool: ConnectionPool | None = None


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected_hex = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, expected_hex)


def init_pool() -> ConnectionPool:
    global _pool
    if _pool is not None:
        return _pool

    last_err: Exception | None = None
    for _ in range(25):
        try:
            pool = ConnectionPool(
                conninfo=DATABASE_URL,
                min_size=1,
                max_size=10,
                kwargs={"row_factory": dict_row},
                open=True,
            )
            with pool.connection() as conn:
                conn.execute("SELECT 1")
            _pool = pool
            return _pool
        except Exception as exc:
            last_err = exc
            time.sleep(1)
    raise RuntimeError(f"No se pudo conectar a PostgreSQL: {last_err}")


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_conn():
    pool = init_pool()
    with pool.connection() as conn:
        yield conn


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS company_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    name TEXT NOT NULL,
    slogan TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    website TEXT NOT NULL,
    branches TEXT NOT NULL,
    employees_count INTEGER NOT NULL DEFAULT 70,
    founded_date TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    consulting_team TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    role_label TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    can_write BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    folio TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    norms TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    elaborated_by TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    elaborated_date TEXT NOT NULL,
    approved_date TEXT NOT NULL,
    summary TEXT NOT NULL,
    content_html TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processes (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    process_type TEXT NOT NULL,
    owner_area TEXT NOT NULL,
    edition TEXT NOT NULL,
    review_date TEXT NOT NULL,
    objective TEXT NOT NULL,
    scope TEXT NOT NULL,
    interactions TEXT NOT NULL,
    flow_steps JSONB NOT NULL,
    inputs TEXT NOT NULL,
    outputs TEXT NOT NULL,
    receivers TEXT NOT NULL,
    kpis JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    related_process TEXT NOT NULL,
    owner_role TEXT NOT NULL,
    classification TEXT NOT NULL,
    cid_c TEXT NOT NULL,
    cid_i TEXT NOT NULL,
    cid_d TEXT NOT NULL,
    protection_level TEXT NOT NULL,
    location TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Activo'
);

CREATE TABLE IF NOT EXISTS risks (
    id SERIAL PRIMARY KEY,
    risk_num INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    risk_type TEXT NOT NULL,
    affects_cid TEXT NOT NULL,
    related_assets TEXT NOT NULL,
    vulnerability TEXT NOT NULL,
    threat TEXT NOT NULL,
    existing_controls TEXT NOT NULL,
    owner_role TEXT NOT NULL,
    impact INTEGER NOT NULL,
    probability INTEGER NOT NULL,
    level INTEGER NOT NULL,
    semaphore TEXT NOT NULL,
    strategy TEXT NOT NULL,
    treatment_plan TEXT NOT NULL,
    treatment_responsible TEXT NOT NULL,
    treatment_deadline TEXT NOT NULL,
    treatment_status TEXT NOT NULL DEFAULT 'En progreso',
    residual_impact INTEGER NOT NULL DEFAULT 2,
    residual_probability INTEGER NOT NULL DEFAULT 2
);

CREATE TABLE IF NOT EXISTS dda_controls (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    decision TEXT NOT NULL,
    justification TEXT NOT NULL,
    related_risks TEXT NOT NULL,
    implementation_status TEXT NOT NULL DEFAULT 'Implementado',
    evidence_ref TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS traceability (
    id SERIAL PRIMARY KEY,
    risk_id INTEGER NOT NULL,
    origin_req TEXT NOT NULL,
    controls TEXT NOT NULL,
    cobit_ref TEXT NOT NULL,
    procedure_code TEXT NOT NULL,
    record_code TEXT NOT NULL,
    kpi_target TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    folio TEXT UNIQUE NOT NULL,
    branch TEXT NOT NULL,
    asset_code TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    sla_hours INTEGER NOT NULL DEFAULT 2,
    status TEXT NOT NULL DEFAULT 'Abierto',
    reported_by TEXT NOT NULL,
    assigned_to TEXT NOT NULL,
    resolution_notes TEXT NOT NULL DEFAULT '',
    lesson_learned TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS cold_chain_logs (
    id SERIAL PRIMARY KEY,
    branch TEXT NOT NULL,
    unit_name TEXT NOT NULL,
    temp_c NUMERIC(5,2) NOT NULL,
    min_c NUMERIC(5,2) NOT NULL,
    max_c NUMERIC(5,2) NOT NULL,
    in_range BOOLEAN NOT NULL,
    corrective_action TEXT NOT NULL DEFAULT '',
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS backups (
    id SERIAL PRIMARY KEY,
    backup_date TEXT NOT NULL,
    scope TEXT NOT NULL,
    destination TEXT NOT NULL,
    restore_tested BOOLEAN NOT NULL DEFAULT FALSE,
    restore_result TEXT NOT NULL,
    responsible TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS access_reviews (
    id SERIAL PRIMARY KEY,
    employee_name TEXT NOT NULL,
    role_area TEXT NOT NULL,
    branch TEXT NOT NULL,
    system_name TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_date TEXT NOT NULL,
    verified_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Completado'
);

CREATE TABLE IF NOT EXISTS trainings (
    id SERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    norm_ref TEXT NOT NULL,
    session_date TEXT NOT NULL,
    facilitator TEXT NOT NULL,
    attendees_count INTEGER NOT NULL,
    target_count INTEGER NOT NULL,
    branch TEXT NOT NULL,
    evidence_note TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    service_type TEXT NOT NULL,
    sla_target TEXT NOT NULL,
    nda_signed BOOLEAN NOT NULL DEFAULT TRUE,
    last_eval_date TEXT NOT NULL,
    compliance_status TEXT NOT NULL DEFAULT 'Cumple',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_findings (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    norm_clause TEXT NOT NULL,
    area_process TEXT NOT NULL,
    finding_type TEXT NOT NULL,
    description TEXT NOT NULL,
    root_cause TEXT NOT NULL DEFAULT '',
    corrective_action TEXT NOT NULL DEFAULT '',
    responsible TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Abierta',
    audit_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cfdi_requests (
    id SERIAL PRIMARY KEY,
    ticket_folio TEXT NOT NULL,
    branch TEXT NOT NULL,
    rfc TEXT NOT NULL,
    razon_social TEXT NOT NULL,
    email TEXT NOT NULL,
    total_mxn NUMERIC(10,2) NOT NULL,
    nom151_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Timbrado y Resguardado (NOM-151)',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_trail (
    id SERIAL PRIMARY KEY,
    actor_email TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""


def init_schema_and_seed() -> None:
    from app.seed_data import seed_database

    with get_conn() as conn:
        conn.execute(SCHEMA_SQL)
        conn.commit()
    seed_database()


def log_audit(conn, user: dict | None, action: str, entity: str, detail: str) -> None:
    email = user["email"] if user else "sistema@lafincadelbarriocol.com"
    role = user["role_label"] if user else "Sistema"
    conn.execute(
        """
        INSERT INTO audit_trail (actor_email, actor_role, action, entity, detail)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (email, role, action, entity, detail),
    )
