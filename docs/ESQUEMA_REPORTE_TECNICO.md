# Estructura y Borrador Base — Reporte Técnico (3ª Parcial)

> Documento de apoyo para generar el **Reporte Técnico en PDF** (fecha límite: **lunes 23 de noviembre, 10:00 AM**).

---

## 1. Portada Obligatoria (Página 1)

### Datos de la Empresa
- **Nombre:** La Finca del Barrio (*"Amigos atendiendo amigos"*)
- **Domicilio:** Blvrd Camino Real #549, Col. El Diezmo, C.P. 28010, Colima, Col., México
- **Teléfono:** 312 133 2206
- **Correo electrónico:** `lafincadelbarrio@gmail.com`
- **Sitio web:** `https://www.lafincadelbarriocol.com/`

### Ingenieros que elaboraron el reporte (*Innova Tec Consultoría en TI*)
- **Carbajal Oseguera Alonso Emiliano** — Líder de Activos y Riesgos (`acarbajal2@ucol.mx`)
- **García Gutiérrez César Emilio** — CISO · Seguridad y Cumplimiento (`cgarcia75@ucol.mx`)
- **Guerrero Mancilla Ángel Daniel** — Owner del Proyecto · Gobierno de TI (`aguerrero36@ucol.mx`)
- **Terríquez Cárdenas Benjamín** — Líder de Procesos y Entrega (`bterriquez@ucol.mx`)
- **Institución:** Universidad de Colima · Facultad de Telemática · Ingeniería en Software
- **Materia:** Gestión de las Tecnologías de Información · Docente: Glenda Margarita Mayoral Baldivia

---

## 2. Índice Sugerido del Reporte Técnico

1. **Introducción y Alcance del Sistema (`LFB-ALC-01`)**
   - Cobertura: Sucursal Camino Real, Sucursal Terraza San Fernando, marca hermana *La Finca del Toro* y eventos/ferias.
   - Diagnóstico del sitio público actual (`lafincadelbarriocol.com`) vs. necesidad de intranet SGI segregada (Control `5.15`).
2. **Arquitectura de Software y Herramientas Utilizadas**
   - **Backend:** Python 3.12 + **FastAPI** + API REST documentada automáticamente en `/docs` (OpenAPI/Swagger).
   - **Frontend:** **Jinja2** (SSR) + **HTMX 2.0.4** (interacciones parciales sin SPA pesada) + **Tailwind CSS 3.4** compilado localmente (cero dependencia de CDN).
   - **Base de datos:** **PostgreSQL 16** (`psycopg3` con pool de conexiones) y volumen persistente `lfb_postgres_data`.
   - **Contenedorización y Operación Offline:** Construcción multi-stage en **Docker / Podman** (`Dockerfile` + `docker-compose.yml` + `scripts/run-containers.sh`), operando 100 % local en `http://localhost:8080` sin depender de conectividad Wi-Fi.
   - **Seguridad aplicada en la herramienta:**
     - Hashing de contraseñas con **PBKDF2-HMAC-SHA256** (120,000 iteraciones + salt aleatorio).
     - Cookies de sesión firmadas (`itsdangerous` HMAC, `HttpOnly`, `SameSite=Lax`).
     - Control de acceso basado en roles (**RBAC**): escritura para roles internos y modo **solo lectura (HTTP 403)** para *Auditor Externo* (Controles `5.15` y `5.18`).
     - Bitácora inmutable de actividad (`audit_trail`) en PostgreSQL (Controles `8.15` y `8.16`).
     - Datos de prueba ficticios en módulos de cliente (Control `8.33`) y separación de entorno (Control `8.31`).
3. **Alineación Técnica a Normas y Marcos**
   - **ISO/IEC 27001:2022:** Cláusulas 4–10, matriz de 12 riesgos (`LFB-MCGR-01`), inventario de 20 activos (`ACT-01..20`), DdA de 93 controles (`50` aplican, `37` parciales, `6` no aplican).
   - **ISO 22000:2018 + NOM-251:** Módulo de Bitácora Tecnológica de Cadena de Frío (`FR-CA-02`) vinculado al Control `8.16` (alerta automática y generación de ticket crítico al salir de rango `-2 °C a 4 °C`).
   - **ISO/IEC 38500:2024:** Tablero Directivo de KPIs y Acta de Revisión por la Dirección (`LFB-ACT-RD-01`).
   - **ITIL 4 y COBIT 2019:** Mesa de Ayuda (`FR-TI-01`, SLA `< 2 h` críticos / `< 24 h` normales, lecciones aprendidas) mapeada a `APO12`, `DSS02`, `DSS04` y `BAI09`.
   - **Normatividad Mexicana:** Portal CFDI demostrativo con sello de integridad **NOM-151-SCFI-2016** y Aviso **LFPDPPP**.
4. **Información Documentada y Formatos Controlados**
   - Estructura institucional (`Código`, `Folio`, `Versión`, `Elaboró`, `Revisó`, `Autorizó`), con exportación oficial a PDF desde `/documentos/{code}/imprimir` y respaldo completo JSON desde `/api/export/expediente.json`.
   - Capturas de pantalla de cada módulo en ejecución + pruebas automatizadas (`pytest`).
