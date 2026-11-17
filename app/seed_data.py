import json
from pathlib import Path
from app.db import get_conn, hash_password

DATA_PATH = Path(__file__).resolve().parent / "data" / "fase1_extracted.json"


def _doc_html(sections: list[tuple[str, str]]) -> str:
    parts = []
    for title, body in sections:
        parts.append(
            f'<section class="mb-5">'
            f'<h3 class="text-base font-bold text-vino-800 border-b border-crema-200 pb-1 mb-2">{title}</h3>'
            f'<div class="text-sm text-stone-700 leading-relaxed space-y-2">{body}</div>'
            f'</section>'
        )
    return "\n".join(parts)


def seed_database() -> None:
    with get_conn() as conn:
        existing = conn.execute("SELECT COUNT(*) AS c FROM company_settings").fetchone()["c"]
        if existing > 0:
            return

        # 1. Company settings (real data from lafincadelbarriocol.com + Parcial 1 docs)
        conn.execute(
            """
            INSERT INTO company_settings (
                id, name, slogan, address, phone, email, website,
                branches, employees_count, founded_date, owner_name, consulting_team
            ) VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "La Finca del Barrio",
                "Amigos atendiendo amigos",
                "Blvrd Camino Real #549, Col. El Diezmo, C.P. 28010, Colima, Col., México",
                "312 133 2206",
                "lafincadelbarrio@gmail.com",
                "https://www.lafincadelbarriocol.com/",
                "Sucursal Camino Real, Sucursal Terraza San Fernando, Marca hermana La Finca del Toro y Eventos/Ferias",
                70,
                "17 de noviembre de 2018",
                "Ramón del Toro",
                "Innova Tec Consultoría en TI (Carbajal, García, Guerrero, Terríquez)",
            ),
        )

        # 2. Users & Roles (Control 5.15 & 5.18)
        default_pw = hash_password("FincaSGI2026!")
        users = [
            ("cgarcia75@ucol.mx", "César Emilio García Gutiérrez", "ciso", "CISO · Seguridad y Cumplimiento", default_pw, True),
            ("acarbajal2@ucol.mx", "Alonso Emiliano Carbajal Oseguera", "activos_riesgos", "Líder de Activos y Riesgos", default_pw, True),
            ("aguerrero36@ucol.mx", "Ángel Daniel Guerrero Mancilla", "owner", "Owner del Proyecto · Gobierno de TI", default_pw, True),
            ("bterriquez@ucol.mx", "Benjamín Terríquez Cárdenas", "procesos", "Líder de Procesos y Entrega", default_pw, True),
            ("direccion@lafincadelbarriocol.com", "Ramón del Toro", "direccion", "Dirección General / Dueño", default_pw, True),
            ("auditor@evaluacion.ucol.mx", "Equipo Auditor Externo", "auditor", "Auditor Externo (Solo Lectura)", default_pw, False),
        ]
        for u in users:
            conn.execute(
                """
                INSERT INTO users (email, full_name, role, role_label, password_hash, can_write)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                u,
            )

        # 3. 20 Assets (ACT-01..ACT-20 from 2.2-ACTIVOS_GTI.pdf)
        assets = [
            ("ACT-01", "Terminal y Hardware POS", "Hardware", "Facturación y Cobro, Atención al Cliente", "Gerente de sucursal", "Restringido", "Medio", "Alto", "Alto", "Acceso físico controlado, mantenimiento preventivo y terminal de respaldo", "Camino Real / San Fernando"),
            ("ACT-02", "Software de Punto de Venta (POS)", "Software", "Facturación y Cobro, Atención al Cliente", "Gerente de sucursal", "Restringido", "Alto", "Alto", "Alto", "Contraseña individual, credenciales por rol, respaldo diario y modo offline", "Camino Real / San Fernando / Finca del Toro"),
            ("ACT-03", "Software de facturación electrónica (CFDI)", "Software", "Facturación y Cobro", "Administración", "Restringido", "Alto", "Alto", "Medio", "Cifrado, respaldo conforme a NOM-151, acceso restringido", "Administración Central"),
            ("ACT-04", "Base de datos de clientes (reservaciones, contacto)", "Información", "Atención al Cliente", "Gerente de sucursal", "Restringido", "Alto", "Medio", "Medio", "Acceso limitado, cifrado y cumplimiento LFPDPPP", "Nube / Portal Web"),
            ("ACT-05", "Base de datos de proveedores y catálogo de insumos", "Información", "Compra y Abastecimiento", "Encargado de compras", "Interno", "Medio", "Alto", "Medio", "Acceso solo a personal de compras/cocina", "Administración Central"),
            ("ACT-06", "Registro de inventario de insumos y cortes", "Información", "Compra y Abastecimiento", "Encargado de compras", "Interno", "Medio", "Alto", "Alto", "Actualización diaria, respaldo semanal", "Ambas sucursales"),
            ("ACT-07", "Sistema digital de gestión de inventarios", "Software", "Compra y Abastecimiento", "Encargado de compras", "Interno", "Medio", "Alto", "Alto", "Control de usuarios, respaldos automatizados", "Nube / POS"),
            ("ACT-08", "Router y red Wi-Fi administrativa", "Componentes de red", "Gestión de TI (transversal)", "Responsable de TI", "Restringido", "Alto", "Alto", "Alto", "Contraseña robusta con rotación trimestral, red aislada de clientes", "Camino Real / San Fernando"),
            ("ACT-09", "Red Wi-Fi de clientes", "Componentes de red", "Atención al Cliente", "Responsable de TI", "Público", "Bajo", "Bajo", "Medio", "VLAN aislada de la administrativa, sin acceso a POS", "Salón clientes"),
            ("ACT-10", "Cámaras de videovigilancia", "Hardware", "Gestión de TI (transversal)", "Gerente de sucursal", "Restringido", "Alto", "Medio", "Medio", "Acceso solo a gerencia, respaldo de grabaciones 30 días", "Cocina / Caja / Accesos"),
            ("ACT-11", "Computadora(s) administrativa(s)", "Hardware", "Gestión de TI, Facturación", "Responsable de TI", "Restringido", "Alto", "Alto", "Alto", "Antivirus, contraseña robusta, actualización de software", "Oficina administrativa"),
            ("ACT-12", "Impresora de comandas/tickets", "Hardware", "Atención al Cliente", "Gerente de sucursal", "Interno", "Bajo", "Medio", "Alto", "Mantenimiento preventivo, acceso físico controlado", "Cocina / Barra / Caja"),
            ("ACT-13", "Celulares / tablets de trabajo (pedidos, delivery)", "Hardware", "Atención al Cliente, Compra", "Gerente de sucursal", "Interno", "Medio", "Medio", "Alto", "Bloqueo con contraseña, MDM/localización remota, solo apps autorizadas", "Piso / Eventos"),
            ("ACT-14", "Sistema de mesa de ayuda e incidencias internas", "Software", "Gestión de TI", "Responsable de TI", "Interno", "Medio", "Medio", "Medio", "Bitácora de incidencias (FR-TI-01), control de acceso por rol", "Intranet SGI"),
            ("ACT-15", "Servicio de soporte técnico y mesa de ayuda externa", "Servicios", "Gestión de TI", "Responsable de TI", "Interno", "Medio", "Alto", "Alto", "Acuerdos de nivel de servicio (SLA ≤ 4 h), NDA y acceso supervisado", "Proveedores TI"),
            ("ACT-16", "Registros contables y estados financieros", "Información", "Facturación y Cobro", "Administración", "Restringido", "Alto", "Alto", "Alto", "Acceso solo a dueño/administración, respaldo externo cifrado", "Administración / Nube"),
            ("ACT-17", "Personal capacitado (meseros, cocina, caja, TI)", "Personas", "Todos los procesos", "Gerencia / RH", "Interno", "Medio", "Alto", "Alto", "Capacitación anual en políticas TI, inocuidad y control de accesos por rol", "70 empleados"),
            ("ACT-18", "Imagen de marca y reputación (La Finca del Barrio)", "Intangibles", "Todos los procesos", "Dueño (Ramón del Toro)", "Interno", "Medio", "Alto", "Alto", "Monitoreo de redes sociales, protocolo de manejo de crisis (PR-DI-01)", "Marca / Redes"),
            ("ACT-19", "Contratos con proveedores de carne/insumos", "Información", "Compra y Abastecimiento", "Encargado de compras", "Restringido", "Alto", "Alto", "Medio", "Resguardo físico/digital, acceso solo a administración y compras", "Archivo central"),
            ("ACT-20", "Servicio de plataformas de delivery (apps externas)", "Servicios", "Atención al Cliente", "Gerente de sucursal", "Interno", "Medio", "Alto", "Alto", "Verificación periódica de conciliación de pedidos y pagos", "Integración Delivery"),
        ]
        for a in assets:
            conn.execute(
                """
                INSERT INTO assets (
                    code, name, category, related_process, owner_role,
                    classification, cid_c, cid_i, cid_d, protection_level, location
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                a,
            )

        # 4. 4 Complete Processes (LFB-CP-01..04, closing "por definir" from Fase 1)
        processes = [
            (
                "LFB-CP-01",
                "Compra y Abastecimiento de Insumos",
                "Clave",
                "Cocina / Administración",
                "02",
                "17/11/2026",
                "Garantizar el abastecimiento oportuno y de calidad (cortes finos e insumos) para las 2 sucursales y La Finca del Toro, asegurando cadena de frío y evitando desabasto.",
                "Desde la detección del nivel mínimo de inventario hasta la recepción, verificación térmica, registro en POS y almacenamiento.",
                "Atención al Cliente (disponibilidad), Gestión de TI (inventario/sensores), Facturación y Cobro (costeo).",
                json.dumps([
                    "Revisar inventario por sucursal",
                    "¿Nivel bajo mínimo?",
                    "Generar orden de compra a proveedor certificado",
                    "Verificar pedido, calidad y temperatura (≤ 4 °C)",
                    "¿Cumple criterios? (Si no: rechazar y registrar incidencia)",
                    "Registrar entrada en POS y actualizar costo"
                ]),
                "Solicitud de compra por mínimo de inventario, catálogo y evaluación de proveedores.",
                "Insumo recibido, verificado en cadena de frío y registrado en el sistema.",
                "Cocina, Facturación y Cobro.",
                json.dumps([
                    {"name": "Entrega en tiempo y forma", "target": "≥ 90%", "freq": "Mensual"},
                    {"name": "Insumos rechazados por calidad", "target": "< 5%", "freq": "Mensual"},
                    {"name": "Rupturas de stock (desabasto)", "target": "0 / semana", "freq": "Semanal"},
                    {"name": "Rupturas de cadena de frío", "target": "0 eventos", "freq": "Diaria"},
                ]),
            ),
            (
                "LFB-CP-02",
                "Gestión de TI — Soporte y Mantenimiento de Sistemas",
                "Apoyo",
                "Área de Gestión de TI",
                "02",
                "17/11/2026",
                "Garantizar la continuidad, seguridad y disponibilidad de POS, red administrativa, cámaras, sensores de frío y facturación electrónica en sucursales y eventos.",
                "Desde la detección o reporte de falla / solicitud de cambio hasta la resolución, documentación y lección aprendida (ITIL 4).",
                "Compra y Abastecimiento, Atención al Cliente, Facturación y Cobro, Dirección (ISO 38500).",
                json.dumps([
                    "Detectar o reportar falla (POS, red, sensores, CFDI)",
                    "Registrar ticket en Mesa de Ayuda (FR-TI-01)",
                    "Clasificar severidad: ¿Es crítica? (No: programar <24h)",
                    "Activar contingencia si es crítica (modo offline / terminal respaldo)",
                    "Diagnosticar causa raíz y aplicar solución",
                    "Verificar operación, documentar lección aprendida y cerrar"
                ]),
                "Reporte de falla de sucursal, alertas de monitoreo/temperatura, solicitudes de mantenimiento.",
                "Sistema operativo, ticket cerrado con evidencia y métrica SLA.",
                "Todas las áreas de sucursal, Administración y Dirección.",
                json.dumps([
                    {"name": "Resolución de fallas críticas", "target": "< 2 horas", "freq": "Por incidente"},
                    {"name": "Resolución de fallas no críticas", "target": "< 24 horas", "freq": "Por incidente"},
                    {"name": "Disponibilidad del sistema POS", "target": "≥ 99%", "freq": "Mensual"},
                    {"name": "Mantenimiento preventivo trimestral", "target": "100%", "freq": "Trimestral"},
                ]),
            ),
            (
                "LFB-CP-03",
                "Atención al Cliente y Servicio en Salón",
                "Clave",
                "Gerente de Sucursal",
                "02",
                "17/11/2026",
                "Brindar una atención cálida y oportuna ('Amigos atendiendo amigos'), asegurando la toma exacta de comandas, cortes en el término solicitado y protección de datos de reserva.",
                "Desde la reservación o recepción del comensal hasta el servicio en mesa, entrega a domicilio/eventos y solicitud de cuenta.",
                "Compra y Abastecimiento (insumos listos), Facturación y Cobro (cierre de cuenta), Gestión de TI (POS/comandas/tablets).",
                json.dumps([
                    "Recibir al cliente o validar reservación (LFPDPPP)",
                    "Tomar comanda en POS / tablet autorizada",
                    "Aplicar checklist de verificación antes de enviar a cocina",
                    "Preparar y emplatar corte en término exacto",
                    "Entregar servicio en salón o delivery conciliado",
                    "Solicitar cuenta y despedir al comensal"
                ]),
                "Llegada o reservación del cliente, menú actualizado, insumos disponibles.",
                "Servicio entregado conforme al pedido y cuenta abierta para cobro.",
                "Comensal, Área de Facturación y Cobro.",
                json.dumps([
                    {"name": "Errores de comanda por semana", "target": "≤ 2 (tendencia a la baja)", "freq": "Semanal"},
                    {"name": "Tiempo promedio de entrega de platillos", "target": "≤ 22 minutos", "freq": "Semanal"},
                    {"name": "Cortes entregados en término solicitado", "target": "≥ 97%", "freq": "Semanal"},
                    {"name": "Satisfacción / quejas críticas en redes", "target": "< 1% de órdenes", "freq": "Mensual"},
                ]),
            ),
            (
                "LFB-CP-04",
                "Facturación y Cobro",
                "Clave",
                "Administración",
                "02",
                "17/11/2026",
                "Cobrar correctamente cada cuenta en salón, domicilio o eventos, y emitir/resguardar los CFDI de ambas marcas conforme al SAT y la NOM-151.",
                "Desde el cierre de cuenta en POS hasta el cobro, timbrado CFDI (si se solicita), resguardo cifrado y corte diario de ventas.",
                "Atención al Cliente (cuenta), Compra (costos), Gestión de TI (POS, red, software CFDI y respaldos).",
                json.dumps([
                    "Cerrar cuenta en POS y presentar total al cliente",
                    "Procesar pago (efectivo/terminal o modo offline en contingencia)",
                    "¿Cliente solicita factura CFDI?",
                    "Capturar datos fiscales (RFC) y timbrar CFDI",
                    "Enviar por correo y resguardar XML/PDF conforme NOM-151",
                    "Ejecutar corte diario y respaldo en nube"
                ]),
                "Cuenta cerrada, datos fiscales del cliente (cuando solicita factura), registro de costos.",
                "Pago conciliado, CFDI timbrado y resguardado, reporte diario de ventas.",
                "Cliente, Administración, Dirección y SAT.",
                json.dumps([
                    {"name": "CFDI emitidos y resguardados (NOM-151)", "target": "100%", "freq": "Mensual"},
                    {"name": "Cierre y conciliación diaria de ventas", "target": "100% de días operados", "freq": "Diaria"},
                    {"name": "Disponibilidad del cobro en hora pico", "target": "≥ 99%", "freq": "Mensual"},
                ]),
            ),
        ]
        for p in processes:
            conn.execute(
                """
                INSERT INTO processes (
                    code, name, process_type, owner_area, edition, review_date,
                    objective, scope, interactions, flow_steps, inputs, outputs, receivers, kpis
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb)
                """,
                p,
            )

        # 5. Load Fase 1 extracted JSON (12 risks, 93 DdA, 12 traceability)
        extracted = json.loads(DATA_PATH.read_text(encoding="utf-8"))

        treatment_meta = {
            1: ("Responsable de TI", "30/11/2026", "Implementado", 2, 2),
            2: ("CISO / Administración", "15/12/2026", "En progreso", 3, 2),
            3: ("Administración / TI", "30/11/2026", "Implementado", 2, 1),
            4: ("Responsable de TI", "25/11/2026", "Implementado", 2, 1),
            5: ("Encargado de compras", "10/12/2026", "En progreso", 3, 2),
            6: ("Encargado de compras / TI", "22/11/2026", "Implementado", 3, 1),
            7: ("Gerente de sucursal", "25/11/2026", "Implementado", 2, 2),
            8: ("Responsable de TI", "05/12/2026", "En progreso", 2, 2),
            9: ("Gerente de sucursal", "30/11/2026", "En progreso", 2, 1),
            10: ("Dueño (Ramón del Toro)", "20/11/2026", "Implementado", 2, 2),
            11: ("Administración", "Anual", "Implementado", 3, 1),
            12: ("Responsable de TI", "15/12/2026", "Pendiente", 3, 2),
        }

        for r in extracted["risks"]:
            resp, dl, st, ri, rp = treatment_meta[r["id"]]
            conn.execute(
                """
                INSERT INTO risks (
                    risk_num, title, risk_type, affects_cid, related_assets,
                    vulnerability, threat, existing_controls, owner_role,
                    impact, probability, level, semaphore, strategy, treatment_plan,
                    treatment_responsible, treatment_deadline, treatment_status,
                    residual_impact, residual_probability
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    r["id"], r["risk"], r["type"], r["affects"], r["assets"],
                    r["vulnerability"], r["threat"], r["existing_controls"], r["owner"],
                    r["impact"], r["probability"], r["level"], r["semaphore"], r["strategy"], r["treatment"],
                    resp, dl, st, ri, rp,
                ),
            )

        for c in extracted["dda"]:
            if c["decision"] == "No aplica":
                impl = "No aplica"
            elif c["decision"] == "Aplica":
                impl = "Implementado"
            else:
                impl = "En progreso"
            ev = "SGI Portal / LFB-POL-01" if c["decision"] != "No aplica" else "Justificado en DdA"
            conn.execute(
                """
                INSERT INTO dda_controls (
                    code, name, domain, decision, justification, related_risks, implementation_status, evidence_ref
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (c["code"], c["name"], c["domain"], c["decision"], c["justification"], c["related_risks"], impl, ev),
            )

        for t in extracted["traceability"]:
            conn.execute(
                """
                INSERT INTO traceability (
                    risk_id, origin_req, controls, cobit_ref, procedure_code, record_code, kpi_target
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (t["risk_id"], t["origin_req"], t["controls"], t["cobit"], t["procedure"], t["record_format"], t["kpi"]),
            )

        # 6. Controlled Documents (Cl. 7.5: code, folio, version, dates, Elaboro/Reviso/Autorizo)
        docs = [
            (
                "LFB-ALC-01", "LFB.1.1/GTI/001/2026", "Documento de Alcance del Sistema de Gestión Integral (SGI)",
                "Gobierno y Alcance", "ISO/IEC 27001 Cl. 4.3 · ISO 22000 Cl. 4.3 · ISO/IEC 38500", "v1.0", "Aprobado",
                "César García (CISO)", "Ángel Guerrero (Owner)", "Ramón del Toro (Dirección)",
                "16/11/2026", "17/11/2026",
                "Define los límites físicos, organizacionales y de procesos cubiertos por el SGI en La Finca del Barrio y su marca hermana.",
                _doc_html([
                    ("1. Propósito", "<p>Establecer formalmente el alcance del Sistema de Gestión Integral (SGI) de <strong>La Finca del Barrio</strong>, integrando Seguridad de la Información (ISO/IEC 27001:2022), Inocuidad Alimentaria (ISO 22000:2018) y Gobierno Corporativo de TI (ISO/IEC 38500:2024).</p>"),
                    ("2. Alcance físico y organizacional", "<ul><li><strong>Sucursal Matriz Camino Real:</strong> Blvrd Camino Real #549, Col. El Diezmo, Colima, Col.</li><li><strong>Sucursal Terraza San Fernando:</strong> Colima, Col.</li><li><strong>Procesos compartidos con La Finca del Toro:</strong> Punto de Venta (POS), inventario central y facturación electrónica CFDI.</li><li><strong>Eventos externos (ferias y festivales):</strong> Incluidos bajo controles portátiles de cadena de frío (FR-CA-02) y terminales de cobro autorizadas (ACT-13).</li></ul>"),
                    ("3. Procesos incluidos", "<p>LFB-CP-01 Compra y Abastecimiento; LFB-CP-02 Gestión de TI (apoyo transversal); LFB-CP-03 Atención al Cliente y Servicio en Salón; LFB-CP-04 Facturación y Cobro.</p>"),
                    ("4. Exclusiones justificadas", "<p>El desarrollo de software subcontratado (control 8.30) y la inteligencia de amenazas especializada (control 5.7) quedan excluidos conforme a la Declaración de Aplicabilidad (DdA_27001) por la escala del negocio y el uso de servicios gestionados.</p>"),
                ]),
            ),
            (
                "LFB-CTX-01", "LFB.1.2/GTI/002/2026", "Análisis de Contexto, Partes Interesadas y FODA del SGI",
                "Gobierno y Alcance", "ISO/IEC 27001 Cl. 4.1–4.2 · ISO 22000 Cl. 4.1–4.2", "v1.0", "Aprobado",
                "Alonso Carbajal (Riesgos)", "Ángel Guerrero (Owner)", "Ramón del Toro (Dirección)",
                "24/09/2026", "17/11/2026",
                "Identifica cuestiones internas y externas, necesidades de partes interesadas y matriz FODA que originan la matriz de riesgos.",
                _doc_html([
                    ("1. Cuestiones internas y externas", "<p><strong>Internas:</strong> ~70 empleados con distintos niveles de cultura digital, operación en 2 sucursales + La Finca del Toro, alta dependencia del POS y de la cadena de frío.</p><p><strong>Externas:</strong> Obligaciones fiscales ante el SAT (CFDI), LFPDPPP, NOM-251-SSA1-2009 (higiene), NOM-151-SCFI-2016 (conservación electrónica), proveedores de internet/energía y presencia digital en lafincadelbarriocol.com.</p>"),
                    ("2. Partes interesadas", "<p><strong>Clientes:</strong> Datos protegidos, cobro ágil, CFDI correcto e inocuidad alimentaria. <strong>Empleados (70):</strong> Herramientas operativas y capacitación. <strong>SAT / Autoridades:</strong> CFDI timbrados y resguardados; cumplimiento sanitario. <strong>Proveedores:</strong> SLA claros y pagos puntuales. <strong>Dirección:</strong> Continuidad operativa y rentabilidad.</p>"),
                    ("3. Matriz FODA de Gestión de TI", "<p><strong>Fortalezas:</strong> Política documentada, inventario de 20 activos, respaldo semanal, videovigilancia. <strong>Debilidades:</strong> Dependencia de energía/red, rotación de personal, falta histórica de sensores automáticos. <strong>Oportunidades:</strong> POS modo offline, alertas IoT de temperatura, intranet SGI. <strong>Amenazas:</strong> Cortes eléctricos, filtración de datos, fallas de proveedor, auditorías SAT.</p>"),
                ]),
            ),
            (
                "LFB-POL-01", "LFB.2.1/GTI/003/2026", "Política Integral de Seguridad de la Información y Gobierno de TI",
                "Políticas", "ISO/IEC 27001 Cl. 5.2 · ISO/IEC 38500 · Control 5.1, 5.10, 5.15", "v1.0", "Aprobado",
                "César García (CISO)", "Ángel Guerrero (Owner)", "Ramón del Toro (Dirección)",
                "02/10/2026", "17/11/2026",
                "Establece los compromisos de la alta dirección y las reglas obligatorias de uso aceptable, accesos, contraseñas y toma de decisiones de TI.",
                _doc_html([
                    ("1. Declaración de la Dirección", "<p>La Dirección General de <strong>La Finca del Barrio</strong> se compromete a proteger la confidencialidad, integridad y disponibilidad de la información de clientes, facturación CFDI e inventarios, garantizar la inocuidad mediante monitoreo tecnológico de la cadena de frío y gobernar las inversiones de TI bajo los 6 principios de ISO/IEC 38500.</p>"),
                    ("2. Lineamientos obligatorios", "<ul><li><strong>Control de acceso (5.15 / 5.18):</strong> Credenciales individuales por rol; prohibido compartir contraseñas de POS. Revocación inmediata en bajas de personal (FR-TI-03).</li><li><strong>Segmentación de red (8.22):</strong> La red Wi-Fi administrativa (ACT-08) está aislada de la red Wi-Fi de clientes (ACT-09).</li><li><strong>Uso aceptable (5.10):</strong> Los equipos de trabajo (ACT-11, ACT-13) se utilizan exclusivamente para operación del restaurante y solo con aplicaciones autorizadas.</li><li><strong>Protección de datos (5.34 / LFPDPPP):</strong> Los datos de reservaciones y CFDI se resguardan con acceso restringido y cifrado.</li></ul>"),
                    ("3. Revisión y sanciones", "<p>Esta política se revisa cada 6 meses o ante cambios mayores. Su incumplimiento deriva en acciones correctivas y medidas administrativas internas.</p>"),
                ]),
            ),
            (
                "LFB-POL-02", "LFB.2.2/GTI/004/2026", "Política de Copias de Seguridad y Continuidad Operativa",
                "Políticas", "ISO/IEC 27001 Controles 5.29, 5.30, 8.13 · COBIT DSS04", "v1.0", "Aprobado",
                "César García (CISO)", "Ángel Guerrero (Owner)", "Ramón del Toro (Dirección)",
                "02/10/2026", "17/11/2026",
                "Define la estrategia 3-2-1 adaptada, RTO/RPO, pruebas semestrales de restauración y operación offline ante caídas de red o energía.",
                _doc_html([
                    ("1. Objetivos de recuperación", "<p><strong>RTO (Tiempo Objetivo de Recuperación):</strong> ≤ 1 hora para cobro en POS. <strong>RPO (Punto Objetivo de Recuperación):</strong> ≤ 24 horas para ventas/POS y ≤ 7 días para respaldos completos administrativos.</p>"),
                    ("2. Esquema de respaldos", "<ul><li>Respaldo diario automático de transacciones POS y CFDI en nube cifrada.</li><li>Respaldo mensual en disco duro externo resguardado bajo llave en Administración.</li><li>Prueba formal de restauración cada 6 meses registrada en formato <strong>FR-TI-02</strong>.</li></ul>"),
                    ("3. Continuidad en hora pico", "<p>Ante fallas de internet o luz, se activa la terminal de respaldo en modo offline y se realiza conciliación al restablecer la red (procedimiento LFB-PR-TI-04).</p>"),
                ]),
            ),
            (
                "LFB-POL-03", "LFB.2.3/GTI/005/2026", "Política de Seguridad en la Relación con Proveedores y SLA",
                "Políticas", "ISO/IEC 27001 Controles 5.19–5.23 · ISO 22000", "v1.0", "Aprobado",
                "Alonso Carbajal (Riesgos)", "César García (CISO)", "Ramón del Toro (Dirección)",
                "02/10/2026", "17/11/2026",
                "Regula los requisitos de disponibilidad, confidencialidad y evaluación anual para proveedores de TI, nube, CFDI e insumos cárnicos.",
                _doc_html([
                    ("1. Acuerdos de Nivel de Servicio (SLA)", "<p>Todo proveedor crítico de TI (POS, internet, facturación CFDI, nube) debe garantizar disponibilidad ≥ 99% y tiempo máximo de respuesta ≤ 4 horas para incidentes críticos.</p>"),
                    ("2. Confidencialidad (NDA)", "<p>Ningún tercero con acceso a datos de clientes, estados financieros o sistemas POS recibirá credenciales sin acuerdo de confidencialidad firmado y acceso supervisado.</p>"),
                    ("3. Proveedores de insumos críticos", "<p>Compras mantendrá al menos un proveedor de respaldo certificado para cortes finos (riesgo #5) y evaluará anualmente su desempeño en <strong>FR-CA-01</strong>.</p>"),
                ]),
            ),
            (
                "LFB-PTR-01", "LFB.3.1/GTI/006/2026", "Metodología de Evaluación y Plan de Tratamiento de Riesgos",
                "Riesgos y Continuidad", "ISO/IEC 27001 Cl. 6.1.2–6.1.3, Cl. 8.2–8.3 · ISO 27005 · COBIT APO12", "v1.0", "Aprobado",
                "Alonso Carbajal (Riesgos)", "César García (CISO)", "Ramón del Toro (Dirección)",
                "07/10/2026", "17/11/2026",
                "Formaliza las escalas semicuantitativas 1–5 (Impacto × Probabilidad), criterios de aceptación y el plan de acción para los 12 riesgos.",
                _doc_html([
                    ("1. Escalas y criterios de aceptación", "<p><strong>Bajo (1–5, Verde):</strong> Aceptable con monitoreo. <strong>Medio (6–12, Amarillo):</strong> Tolerable con controles mitigatorios. <strong>Alto/Crítico (15–25, Rojo):</strong> Inaceptable; requiere tratamiento prioritario inmediato.</p>"),
                    ("2. Riesgos prioritarios (Nivel Alto)", "<ul><li><strong>#1 Falla del POS en hora pico (I=5, P=4 → 20):</strong> Terminal de respaldo + modo offline.</li><li><strong>#6 Ruptura de cadena de frío (I=5, P=4 → 20):</strong> Sensores con alerta automática y bitácora FR-CA-02.</li><li><strong>#2 Filtración de datos/CFDI (I=5, P=3 → 15):</strong> Cifrado BD, control de acceso por rol y capacitación anual.</li></ul>"),
                    ("3. Seguimiento", "<p>El estado de cada tratamiento y el riesgo residual se actualizan en tiempo real en el módulo de Riesgos del Portal SGI y se revisan semestralmente.</p>"),
                ]),
            ),
            (
                "LFB-PR-TI-01", "LFB.4.1/GTI/007/2026", "Procedimiento de Soporte Técnico, Mesa de Ayuda e Incidentes",
                "Procedimientos", "ISO/IEC 27001 Controles 5.24–5.27 · ITIL 4 · ISO/IEC 27035 · COBIT DSS02", "v1.0", "Aprobado",
                "César García (CISO)", "Benjamín Terríquez (Procesos)", "Ángel Guerrero (Owner)",
                "16/11/2026", "17/11/2026",
                "Describe el flujo operativo para registrar, priorizar, atender y documentar incidentes tecnológicos en el formato FR-TI-01.",
                _doc_html([
                    ("1. Clasificación de severidad", "<p><strong>Crítica (SLA < 2 h):</strong> Caída de POS en horario de servicio, falla de facturación CFDI, incidente de seguridad/fuga o caída total de red. <strong>Alta/Normal (SLA < 24 h):</strong> Impresora secundaria, ajustes de catálogo, dudas operativas.</p>"),
                    ("2. Flujo de atención", "<p>1) Personal de sucursal reporta inmediatamente al Responsable de TI y registra folio en <strong>FR-TI-01</strong>. 2) Si es falla de POS, Gerente activa terminal de respaldo/offline. 3) TI diagnostica causa raíz o escala al proveedor bajo SLA. 4) Al resolver, se registra la lección aprendida (mejora continua ITIL 4) y se cierra el ticket.</p>"),
                ]),
            ),
            (
                "LFB-PR-TI-02", "LFB.4.2/GTI/008/2026", "Procedimiento de Respaldo y Pruebas de Restauración",
                "Procedimientos", "ISO/IEC 27001 Control 8.13 · COBIT DSS04", "v1.0", "Aprobado",
                "César García (CISO)", "Alonso Carbajal (Riesgos)", "Ángel Guerrero (Owner)",
                "16/11/2026", "17/11/2026",
                "Detalla la ejecución de respaldos diarios/semanales/mensuales y la verificación semestral de restauración en FR-TI-02.",
                _doc_html([
                    ("1. Frecuencia", "<p>Diaria incremental en nube para POS/CFDI; semanal completa para inventarios y base de clientes; mensual en disco externo cifrado.</p>"),
                    ("2. Prueba de restauración (obligatoria)", "<p>Cada 6 meses se selecciona un respaldo aleatorio y se restaura en entorno de prueba (control 8.31) verificando integridad de registros y registrando el resultado en <strong>FR-TI-02</strong>.</p>"),
                ]),
            ),
            (
                "LFB-PR-TI-03", "LFB.4.3/GTI/009/2026", "Procedimiento de Gestión de Activos y Control de Accesos",
                "Procedimientos", "ISO/IEC 27001 Controles 5.9, 5.11, 5.15, 5.18, 8.1 · COBIT BAI09", "v1.0", "Aprobado",
                "Alonso Carbajal (Riesgos)", "César García (CISO)", "Ángel Guerrero (Owner)",
                "16/11/2026", "17/11/2026",
                "Regula el etiquetado de activos (ACT-01..20), entrega de equipos (FR-TI-04) y altas/bajas de credenciales (FR-TI-03).",
                _doc_html([
                    ("1. Ciclo de vida de activos", "<p>Todo equipo o software crítico recibe código <strong>ACT-XX</strong>, propietario, clasificación (Público/Interno/Restringido) e impacto CID antes de entrar en operación.</p>"),
                    ("2. Altas y bajas de acceso", "<p>Al ingresar personal, Gerencia solicita alta con privilegios mínimos por rol. Al causar baja, TI revoca accesos al POS, Wi-Fi y nube el mismo día y recaba el equipo físico registrándolo en <strong>FR-TI-03</strong>.</p>"),
                ]),
            ),
            (
                "LFB-PR-TI-04", "LFB.4.4/GTI/010/2026", "Plan de Continuidad Operativa ante Fallas Críticas",
                "Procedimientos", "ISO/IEC 27001 Controles 5.29, 5.30, 7.11 · COBIT DSS04", "v1.0", "Aprobado",
                "César García (CISO)", "Ángel Guerrero (Owner)", "Ramón del Toro (Dirección)",
                "16/11/2026", "17/11/2026",
                "Establece los pasos inmediatos ante corte eléctrico, caída de internet o falla simultánea de POS en sucursales y ferias.",
                _doc_html([
                    ("1. Escenarios cubiertos", "<p>Corte de internet en hora pico, corte eléctrico prolongado y falla de hardware POS.</p>"),
                    ("2. Protocolo de contingencia", "<p>1) Conmutar POS a modo offline / terminal móvil con datos celulares (ACT-13). 2) Respaldar energía crítica (router, POS y cámaras de refrigeración). 3) Registrar prueba anual de continuidad en <strong>FR-TI-05</strong>.</p>"),
                ]),
            ),
            (
                "LFB-PR-CA-02", "LFB.4.5/GTI/011/2026", "Procedimiento de Control Tecnológico de Cadena de Frío",
                "Procedimientos", "ISO 22000 Cl. 8.2 / 8.5 · ISO/IEC 27001 Control 8.16 · NOM-251", "v1.0", "Aprobado",
                "Benjamín Terríquez (Procesos)", "César García (CISO)", "Ramón del Toro (Dirección)",
                "16/11/2026", "17/11/2026",
                "Integra el monitoreo de temperatura (ISO 22000) con el seguimiento tecnológico de alertas (ISO 27001 Control 8.16) en FR-CA-02.",
                _doc_html([
                    ("1. Rangos aceptables", "<p><strong>Cámaras de refrigeración (cortes frescos):</strong> -2.0 °C a 4.0 °C. <strong>Congeladores:</strong> -20.0 °C a -15.0 °C. <strong>Contenedores portátiles en ferias:</strong> ≤ 4.0 °C.</p>"),
                    ("2. Respuesta ante desviación", "<p>Si una lectura sale de rango en <strong>FR-CA-02</strong>, el sistema genera alerta inmediata, cocina verifica el sello/compresor y se traslada el lote al equipo de respaldo documentando la acción correctiva.</p>"),
                ]),
            ),
            (
                "LFB-PR-SI-01", "LFB.4.6/GTI/012/2026", "Procedimiento de Protección de Datos Personales y Capacitación",
                "Procedimientos", "ISO/IEC 27001 Controles 5.34, 6.3 · LFPDPPP", "v1.0", "Aprobado",
                "César García (CISO)", "Ángel Guerrero (Owner)", "Ramón del Toro (Dirección)",
                "16/11/2026", "17/11/2026",
                "Define el tratamiento de datos de clientes/empleados bajo la LFPDPPP y el programa de concienciación registrado en FR-SI-02.",
                _doc_html([
                    ("1. Protección de datos (LFPDPPP)", "<p>Los datos recabados en reservaciones y facturación se usan exclusivamente para el servicio solicitado, bajo aviso de privacidad publicado y acceso restringido.</p>"),
                    ("2. Programa de capacitación", "<p>Todo el personal (~70 empleados) recibe inducción y refuerzo anual sobre contraseñas, manejo de comandas y protección de datos, con registro en <strong>FR-SI-02</strong>.</p>"),
                ]),
            ),
            (
                "LFB-PR-FC-01", "LFB.4.7/GTI/013/2026", "Procedimiento de Facturación y Resguardo CFDI (NOM-151)",
                "Procedimientos", "ISO/IEC 27001 Controles 5.31, 5.33 · NOM-151 · SAT", "v1.0", "Aprobado",
                "Benjamín Terríquez (Procesos)", "César García (CISO)", "Ramón del Toro (Dirección)",
                "16/11/2026", "17/11/2026",
                "Estandariza la emisión de CFDI para ambas marcas, la conservación íntegra conforme a NOM-151 y el portal de solicitud para clientes.",
                _doc_html([
                    ("1. Emisión y conservación", "<p>Los comprobantes XML y PDF generados por ACT-03 se almacenan con sello de integridad y respaldo externo por al menos 5 años conforme a disposiciones fiscales y NOM-151.</p>"),
                    ("2. Mejora al portal web", "<p>El módulo de Portal Cliente permite validar ticket, capturar RFC y generar solicitud trazable sin exponer datos internos.</p>"),
                ]),
            ),
            (
                "LFB-PR-AUD-01", "LFB.5.1/GTI/014/2026", "Programa de Auditoría Interna Integrada y Mejora Continua",
                "Auditoría y Mejora", "ISO/IEC 27001 Cl. 9.2, 9.3, 10 · ISO 22000 Cl. 9–10 · ISO 38500", "v1.0", "Aprobado",
                "César García (CISO)", "Ángel Guerrero (Owner)", "Ramón del Toro (Dirección)",
                "16/11/2026", "17/11/2026",
                "Unifica en un solo programa semestral la auditoría de las 3 normas y la Revisión por la Dirección anual, evitando duplicidades.",
                _doc_html([
                    ("1. Frecuencia y roles", "<p>Auditoría interna cada 6 meses liderada por el CISO; Revisión por la Dirección anual presidida por Ramón del Toro y el Owner del proyecto.</p>"),
                    ("2. Gestión de No Conformidades (Cl. 10)", "<p>Cada hallazgo se documenta con análisis de causa raíz, acción correctiva, responsable, fecha compromiso y verificación de eficacia en el módulo de Auditoría del SGI.</p>"),
                ]),
            ),
        ]
        for d in docs:
            conn.execute(
                """
                INSERT INTO documents (
                    code, folio, title, category, norms, version, status,
                    elaborated_by, reviewed_by, approved_by, elaborated_date, approved_date,
                    summary, content_html
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                d,
            )

        # 7. Operational Evidences (realistic demo records — no real customer PII)
        incidents = [
            ("INC-2026-001", "Sucursal Camino Real", "ACT-01", "Intermitencia de red en terminal POS caja 1", "Pérdida de conectividad durante corte de cena; se activó modo offline en terminal de respaldo.", "Crítica", 2, "Cerrado", "Gerente Camino Real", "César García (TI)", "Se conmutó a enlace secundario y se sincronizaron 18 tickets offline sin pérdida.", "Mantener batería cargada de terminal móvil ACT-13 antes de las 19:00 hrs."),
            ("INC-2026-002", "Sucursal Terraza San Fernando", "ACT-12", "Atasco en impresora térmica de comandas cocina", "Retraso de 8 minutos en salida de comandas de parrilla.", "Normal", 24, "Cerrado", "Líder de cocina", "Alonso Carbajal (TI)", "Limpieza de cabezal y cambio a impresora auxiliar.", "Incluir revisión de rodillo en checklist semanal de mantenimiento."),
            ("INC-2026-003", "La Finca del Toro", "ACT-03", "Validación de folio CFDI compartido en cierre", "Diferencia de serie fiscal en módulo de facturación.", "Alta", 2, "En atención", "Administración", "César García (TI)", "Revisión de configuración de serie multi-sucursal con soporte del proveedor.", "Documentar matriz de series fiscales en LFB-PR-FC-01."),
        ]
        for inc in incidents:
            conn.execute(
                """
                INSERT INTO incidents (
                    folio, branch, asset_code, title, description, severity, sla_hours,
                    status, reported_by, assigned_to, resolution_notes, lesson_learned,
                    resolved_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CASE WHEN %s = 'Cerrado' THEN NOW() ELSE NULL END)
                """,
                (*inc, inc[7]),
            )

        cold_logs = [
            ("Sucursal Camino Real", "Cámara de Cortes Finos #1", 1.8, -2.0, 4.0, True, "Operación nominal", "Líder de cocina"),
            ("Sucursal Camino Real", "Congelador Principal", -17.5, -20.0, -15.0, True, "Operación nominal", "Líder de cocina"),
            ("Sucursal Terraza San Fernando", "Cámara de Cortes #2", 5.4, -2.0, 4.0, False, "Puerta mal cerrada tras descarga; se selló empaque, se trasladó lote temporal y bajó a 2.1 °C en 15 min.", "Encargado de compras"),
            ("Sucursal Terraza San Fernando", "Cámara de Cortes #2", 2.1, -2.0, 4.0, True, "Verificación post-ajuste correcta", "Encargado de compras"),
            ("Evento Feria Colima", "Contenedor Térmico Móvil A", 2.9, -2.0, 4.0, True, "Monitoreo en evento externo", "Gerente de sucursal"),
        ]
        for cl in cold_logs:
            conn.execute(
                """
                INSERT INTO cold_chain_logs (
                    branch, unit_name, temp_c, min_c, max_c, in_range, corrective_action, recorded_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                cl,
            )

        backups = [
            ("2026-11-15", "Base de datos POS + CFDI (ambas sucursales y Finca del Toro)", "Nube cifrada", True, "Exitosa", "César García", "Prueba semestral verificada en entorno aislado (Control 8.31). Integridad 100%."),
            ("2026-11-08", "Inventarios, recetas estándar y catálogos de proveedores", "Nube cifrada", False, "No probada", "Alonso Carbajal", "Respaldo semanal automático completado."),
            ("2026-11-01", "Cierre contable mensual y XML NOM-151", "Disco externo sucursal", True, "Exitosa", "Administración", "Disco resguardado en caja fuerte administrativa."),
        ]
        for b in backups:
            conn.execute(
                """
                INSERT INTO backups (backup_date, scope, destination, restore_tested, restore_result, responsible, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                b,
            )

        access_rows = [
            ("Juan Pérez (Demo)", "Mesero", "Sucursal Camino Real", "POS Comandas (ACT-02)", "Alta", "2026-11-02", "Gerente de sucursal", "Completado"),
            ("María López (Demo)", "Caja", "Sucursal Terraza San Fernando", "POS / CFDI (ACT-02, ACT-03)", "Revisión periódica", "2026-11-10", "César García (CISO)", "Completado"),
            ("Carlos Ruiz (Demo)", "Ex-auxiliar de barra", "Sucursal Camino Real", "POS / Wi-Fi Admin (ACT-02, ACT-08)", "Baja / Revocación", "2026-11-12", "César García (CISO)", "Completado"),
        ]
        for ar in access_rows:
            conn.execute(
                """
                INSERT INTO access_reviews (employee_name, role_area, branch, system_name, action_type, action_date, verified_by, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                ar,
            )

        trainings = [
            ("Inducción a Política de TI, uso de POS y contraseñas seguras", "ISO 27001 Control 6.3", "2026-10-20", "César García (CISO)", 38, 40, "Sucursal Camino Real", "Lista de asistencia firmada y evaluación 95% aprobada."),
            ("Buenas prácticas de higiene y monitoreo de cadena de frío", "ISO 22000 Cl. 7.2 / NOM-251", "2026-10-27", "Benjamín Terríquez", 28, 30, "Ambas sucursales", "Incluye protocolo de respuesta ante alerta en FR-CA-02."),
            ("Protección de datos de clientes (LFPDPPP) y checklist de comanda", "ISO 27001 Control 5.34", "2026-11-05", "Ángel Guerrero", 24, 25, "Sucursal Terraza San Fernando", "Personal de recepción, caja y meseros."),
        ]
        for tr in trainings:
            conn.execute(
                """
                INSERT INTO trainings (topic, norm_ref, session_date, facilitator, attendees_count, target_count, branch, evidence_note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                tr,
            )

        suppliers = [
            ("Proveedor POS & Nube Gastronómica (Demo)", "Software POS y respaldos", "99.5% disponibilidad · Respuesta < 2 h", True, "2026-11-01", "Cumple", "Contrato y NDA vigentes; modo offline validado."),
            ("PAC Facturación CFDI México (Demo)", "Timbrado CFDI y NOM-151", "99.9% disponibilidad · Timbrado < 3 s", True, "2026-11-01", "Cumple", "Conservación electrónica conforme a NOM-151-SCFI-2016."),
            ("Distribuidora Cárnica del Occidente (Demo)", "Cortes de carne finos", "Entrega en < 24 h · T ≤ 4 °C", True, "2026-11-03", "Cumple", "Se cuenta con segundo proveedor alterno certificado (riesgo #5)."),
            ("Enlace Internet Fibra Empresarial (Demo)", "Conectividad sucursales", "99.0% disponibilidad · Soporte < 4 h", True, "2026-10-28", "Observación", "Se recomienda redundancia LTE para horario pico en Camino Real."),
        ]
        for sp in suppliers:
            conn.execute(
                """
                INSERT INTO suppliers (name, service_type, sla_target, nda_signed, last_eval_date, compliance_status, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                sp,
            )

        findings = [
            ("AUD-2026-01", "ISO 27001 Cl. 7.5", "Control Documental", "Conforme", "Todos los documentos maestros cuentan con código, folio, versión, fechas y firmas de aprobación.", "", "", "César García (CISO)", "2026-11-17", "Cerrada", "2026-11-16"),
            ("AUD-2026-02", "ISO 22000 Cl. 8.5 / 27001 8.16", "Cadena de Frío (Terraza San Fernando)", "No conformidad menor", "Se detectó una desviación a 5.4 °C en Cámara #2 por puerta mal cerrada durante descarga.", "Falta de verificación visual de cierre tras descarga de proveedor.", "Implementar alerta automática en FR-CA-02 y checklist de recepción en LFB-CP-01.", "Encargado de compras", "2026-11-22", "Cerrada", "2026-11-16"),
            ("AUD-2026-03", "ISO 27001 Control 5.34 / LFPDPPP", "Portal Público (lafincadelbarriocol.com)", "Oportunidad de mejora", "El sitio web público actual muestra un correo genérico de plantilla (info@sitio.com) en formularios y carece de módulo de solicitud CFDI.", "Plantilla web comercial sin actualización integral.", "Habilitar Portal de Cumplimiento y Solicitud CFDI en la plataforma SGI y solicitar ajuste en sitio público.", "Ángel Guerrero (Owner)", "2026-11-30", "En seguimiento", "2026-11-16"),
            ("AUD-2026-04", "ISO 27001 Control 5.30", "Continuidad Eléctrica (Riesgo #12)", "Oportunidad de mejora", "Pendiente adquisición física de planta de luz de respaldo para sucursal matriz.", "Presupuesto programado para cierre de año.", "Ejecutar prueba de respaldo con UPS y terminal móvil mientras se aprueba inversión en Revisión por Dirección.", "Ramón del Toro (Dirección)", "2026-12-15", "Abierta", "2026-11-16"),
        ]
        for fd in findings:
            conn.execute(
                """
                INSERT INTO audit_findings (
                    code, norm_clause, area_process, finding_type, description,
                    root_cause, corrective_action, responsible, due_date, status, audit_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                fd,
            )

        cfdi_samples = [
            ("TKT-CR-4091", "Sucursal Camino Real", "XAXX010101000", "Cliente Demostración Colima S.A.", "facturas.demo@ejemplo.mx", 1850.00, "NOM151-SHA256-8F4A2C91E0B3"),
            ("TKT-SF-1822", "Sucursal Terraza San Fernando", "XEXX010101000", "Consultores Demo Occidente S.C.", "contabilidad.demo@ejemplo.mx", 3240.50, "NOM151-SHA256-3D9B7E12C4A8"),
        ]
        for cf in cfdi_samples:
            conn.execute(
                """
                INSERT INTO cfdi_requests (ticket_folio, branch, rfc, razon_social, email, total_mxn, nom151_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                cf,
            )

        conn.execute(
            """
            INSERT INTO audit_trail (actor_email, actor_role, action, entity, detail)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                "cgarcia75@ucol.mx",
                "CISO · Seguridad y Cumplimiento",
                "INICIALIZACION",
                "SGI PostgreSQL",
                "Carga inicial verificada: 20 activos, 12 riesgos, 93 controles DdA, 4 cédulas y 14 documentos controlados.",
            ),
        )
        conn.commit()
