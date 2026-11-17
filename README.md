# Sistema de Gestión Integral (SGI) · La Finca del Barrio

Plataforma web contenedorizada (**FastAPI + HTMX + Tailwind CSS + PostgreSQL**) para operar y evidenciar el Sistema de Gestión Integral de **La Finca del Barrio** alineado a:
- **ISO/IEC 27001:2022** (Seguridad de la Información — 93 controles DdA, riesgos, activos, auditoría y control documental Cl. 7.5)
- **ISO 22000:2018** (Inocuidad Alimentaria — control tecnológico de cadena de frío, cruce con Control 8.16)
- **ISO/IEC 38500:2024** (Gobierno Corporativo de TI — tablero de KPIs y Revisión por la Dirección)
- **ITIL 4 / COBIT 2019** (Mesa de ayuda e incidentes `FR-TI-01`, gestión de activos, respaldos `FR-TI-02` y mejora continua)

## Ejecución 100 % Offline (sin depender de Wi-Fi)

### Opción 1: Docker Compose (estándar)
```bash
docker compose up --build -d
```
Abrir: `http://localhost:8080`

### Opción 2: Podman / Docker sin plugin `compose`
```bash
chmod +x scripts/run-containers.sh
./scripts/run-containers.sh
```
Abrir: `http://localhost:8080` (Documentación OpenAPI en `http://localhost:8080/docs`).

## Cuentas de Demostración (Control de Acceso 5.15 / 5.18)
Contraseña para todas las cuentas: `FincaSGI2026!`
- **CISO (escritura total):** `cgarcia75@ucol.mx`
- **Activos y Riesgos:** `acarbajal2@ucol.mx`
- **Owner:** `aguerrero36@ucol.mx`
- **Procesos:** `bterriquez@ucol.mx`
- **Dirección (Dueño):** `direccion@lafincadelbarriocol.com`
- **Auditor Externo (solo lectura, bloquea mutaciones HTTP 403):** `auditor@evaluacion.ucol.mx`
