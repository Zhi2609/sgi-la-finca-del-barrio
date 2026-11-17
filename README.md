# Sistema de Gestión Integral (SGI) · La Finca del Barrio

Plataforma web contenedorizada (**FastAPI + Jinja2 + HTMX + Tailwind CSS + PostgreSQL 16**) diseñada para operar, organizar y generar evidencia verificable del Sistema de Gestión Integral de **La Finca del Barrio**, funcionando **100 % offline** en contenedor para auditorías y exposiciones.

---

## Empresa Cliente y Equipo Consultor

### Datos de la Empresa
- **Nombre comercial:** La Finca del Barrio (*"Amigos atendiendo amigos"*)
- **Domicilio:** Blvrd Camino Real #549, Col. El Diezmo, C.P. 28010, Colima, Col., México
- **Teléfono:** 312 133 2206
- **Correo electrónico:** `lafincadelbarrio@gmail.com`
- **Sitio web público:** [lafincadelbarriocol.com](https://www.lafincadelbarriocol.com/)
- **Alcance:** Sucursal Camino Real, Sucursal Terraza San Fernando, marca hermana *La Finca del Toro* y eventos/ferias.

### Equipo Consultor (*Innova Tec Consultoría en TI*)
Universidad de Colima · Facultad de Telemática · Ingeniería en Software — *Gestión de las Tecnologías de Información*

| Integrante | Rol en el SGI | Contacto |
| :--- | :--- | :--- |
| Carbajal Oseguera Alonso Emiliano | Líder de Activos y Riesgos | `acarbajal2@ucol.mx` |
| García Gutiérrez César Emilio | CISO · Seguridad y Cumplimiento | `cgarcia75@ucol.mx` |
| Guerrero Mancilla Ángel Daniel | Owner del Proyecto · Gobierno de TI | `aguerrero36@ucol.mx` |
| Terríquez Cárdenas Benjamín | Líder de Procesos y Entrega | `bterriquez@ucol.mx` |

---

## Normas, Marcos y Cumplimiento Integrado

- **ISO/IEC 27001:2022:** Cláusulas 4–10, inventario de 20 activos (`ACT-01..20`), matriz de 12 riesgos (`LFB-MCGR-01`), Declaración de Aplicabilidad (`DdA_27001` con 93 controles), control documental (`Cl. 7.5`) y control de acceso por roles (`5.15` / `5.18`).
- **ISO 22000:2018 + NOM-251-SSA1-2009:** Monitoreo tecnológico de cadena de frío (`FR-CA-02`) integrado con el Control `8.16` de ISO 27001 (alertas y generación automática de ticket crítico al salir de rango `-2 °C a 4 °C`).
- **ISO/IEC 38500:2024:** Tablero ejecutivo de KPIs y Acta de Revisión por la Dirección (`LFB-ACT-RD-01`).
- **ITIL 4 y COBIT 2019:** Mesa de ayuda e incidentes (`FR-TI-01`, SLA `< 2 h` críticos / `< 24 h` normales, lecciones aprendidas) alineada a `APO12`, `DSS02`, `DSS04` y `BAI09`.
- **Normatividad Mexicana (LFPDPPP y NOM-151-SCFI-2016):** Módulo segregado de Portal Cliente para solicitud demostrativa de CFDI con constancia de integridad y aviso de privacidad.

---

## Estructura del Proyecto

```text
sgi-la-finca-del-barrio
├── 📁 app
│   ├── 📁 data
│   │   └── ⚙️ fase1_extracted.json
│   ├── 📁 static
│   │   └── 📁 css
│   │       └── 🎨 input.css
│   ├── 📁 templates
│   │   ├── 📁 partials
│   │   │   ├── 🌐 activos_table.html
│   │   │   └── 🌐 dda_table.html
│   │   ├── 🌐 activos.html
│   │   ├── 🌐 auditoria.html
│   │   ├── 🌐 base.html
│   │   ├── 🌐 cadena_frio.html
│   │   ├── 🌐 config.html
│   │   ├── 🌐 dashboard.html
│   │   ├── 🌐 dda.html
│   │   ├── 🌐 documento_print.html
│   │   ├── 🌐 documentos.html
│   │   ├── 🌐 incidentes.html
│   │   ├── 🌐 login.html
│   │   ├── 🌐 operaciones.html
│   │   ├── 🌐 portal_cliente.html
│   │   ├── 🌐 procesos.html
│   │   ├── 🌐 revision_direccion_print.html
│   │   └── 🌐 riesgos.html
│   ├── 🐍 __init__.py
│   ├── 🐍 config.py
│   ├── 🐍 db.py
│   ├── 🐍 main.py
│   └── 🐍 seed_data.py
├── 📁 docs
│   └── 📝 ESQUEMA_REPORTE_TECNICO.md
├── 📁 scripts
│   └── 📄 run-containers.sh
├── 📁 tests
│   └── 🐍 test_app.py
├── ⚙️ .gitignore
├── 🐳 Dockerfile
├── 📝 README.md
├── ⚙️ docker-compose.yml
├── ⚙️ package.json
├── 📄 requirements.txt
└── 📄 tailwind.config.js
```

---

## Módulos Principales de la Plataforma

| Ruta | Módulo | Evidencia / Norma |
| :--- | :--- | :--- |
| `/` | Tablero Directivo SGI | KPIs en tiempo real, mapa de calor `5×5`, bitácora del sistema (`8.15/8.16`) |
| `/documentos` | Control Documental (`Cl. 7.5`) | 14 documentos oficiales con código, folio, versión, firmas e impresión PDF |
| `/procesos` | Procesos y Cédulas | `LFB-CP-01` a `LFB-CP-04` completas con diagramas de flujo e indicadores |
| `/activos` | Inventario de Activos (`5.9`) | 20 activos (`ACT-01..20`), filtros HTMX y exportación CSV |
| `/riesgos` | Matriz de Riesgos y Tratamiento | 12 riesgos (`LFB-MCGR-01`) con mapa de calor y seguimiento editable |
| `/dda` | DdA, Trazabilidad y RACI | 93 controles del Anexo A, trazabilidad COBIT/KPIs y matriz RACI |
| `/incidentes` | Mesa de Ayuda ITIL 4 (`FR-TI-01`) | Tickets por sucursal/activo, SLA `< 2 h / < 24 h` y lecciones aprendidas |
| `/cadena-frio` | Cadena de Frío (`FR-CA-02`) | Lecturas térmicas con alerta automática y creación de ticket crítico |
| `/operaciones` | Registros Operativos | Respaldos (`FR-TI-02`), Accesos/Bajas (`FR-TI-03`), Capacitaciones (`FR-SI-02`), Proveedores (`FR-CA-01`) |
| `/auditoria` | Auditoría Interna y Mejora | Hallazgos (`Cl. 9–10`), acciones correctivas y Acta de Revisión por Dirección |
| `/portal-cliente` | Mejora a `lafincadelbarriocol.com` | Solicitud CFDI demo (NOM-151), Aviso LFPDPPP y compromiso ISO 22000 |
| `/configuracion` | Datos Institucionales | Edición de portada/encabezados y consulta del equipo consultor |

---

## Ejecución 100 % Offline (sin depender de Wi-Fi)

El `Dockerfile` multi-stage compila Tailwind CSS y empaqueta `htmx.min.js` dentro de la imagen en tiempo de construcción, por lo que en ejecución no realiza peticiones a CDNs externos.

### Opción 1: Docker Compose (estándar)
```bash
docker compose up --build -d
```

### Opción 2: Podman / Docker sin plugin `compose`
```bash
chmod +x scripts/run-containers.sh
./scripts/run-containers.sh
```

Una vez levantados `lfb-sgi-db` (`postgres:16-alpine`) y `lfb-sgi-app`:
- **Aplicación web:** `http://localhost:8080`
- **Documentación API (Swagger/OpenAPI):** `http://localhost:8080/docs`
- **Exportación JSON del expediente completo:** `http://localhost:8080/api/export/expediente.json`

---

## Cuentas de Demostración (Control de Acceso `5.15` / `5.18`)

Contraseña para todas las cuentas: `FincaSGI2026!`

| Correo | Rol | Permisos |
| :--- | :--- | :--- |
| `cgarcia75@ucol.mx` | CISO · Seguridad y Cumplimiento | Lectura y escritura total |
| `acarbajal2@ucol.mx` | Líder de Activos y Riesgos | Lectura y escritura |
| `aguerrero36@ucol.mx` | Owner del Proyecto · Gobierno de TI | Lectura y escritura |
| `bterriquez@ucol.mx` | Líder de Procesos y Entrega | Lectura y escritura |
| `direccion@lafincadelbarriocol.com` | Dirección General / Dueño | Lectura y escritura |
| `auditor@evaluacion.ucol.mx` | Auditor Externo | **Solo lectura** (mutaciones bloqueadas con `HTTP 403`) |

---

## Pruebas Automatizadas

Con los contenedores en ejecución:
```bash
docker cp tests lfb-sgi-app:/app/tests
docker exec -e TEST_BASE_URL=http://127.0.0.1:8000 lfb-sgi-app pytest -v /app/tests/test_app.py
```
