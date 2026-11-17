import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sgi_user:sgi_finca_2026_password@localhost:5432/sgi_finca",
)
SESSION_SECRET = os.getenv("SESSION_SECRET", "lfb-sgi-colima-2026-secret-key")
APP_TITLE = "SGI · La Finca del Barrio"
APP_VERSION = "1.0.0"

TEAM_ENGINEERS = [
    {
        "name": "Carbajal Oseguera Alonso Emiliano",
        "role": "Líder de Activos y Riesgos",
        "email": "acarbajal2@ucol.mx",
    },
    {
        "name": "García Gutiérrez César Emilio",
        "role": "CISO · Seguridad y Cumplimiento",
        "email": "cgarcia75@ucol.mx",
    },
    {
        "name": "Guerrero Mancilla Ángel Daniel",
        "role": "Owner del Proyecto · Gobierno de TI",
        "email": "aguerrero36@ucol.mx",
    },
    {
        "name": "Terríquez Cárdenas Benjamín",
        "role": "Líder de Procesos y Entrega",
        "email": "bterriquez@ucol.mx",
    },
]
