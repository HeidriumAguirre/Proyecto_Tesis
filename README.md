# ITS RAG Math — Colegio Murialdo Valparaíso

Sistema de Tutoría Inteligente (ITS) inclusivo para estudiantes del Programa de Integración Escolar (PIE), construido sobre una arquitectura Retrieval-Augmented Generation (RAG) con documentos oficiales del Ministerio de Educación de Chile, integración multimodal con Gemini 2.5 Flash (texto + voz), y reglas pedagógicas explícitas por diagnóstico PIE (TEA, TDAH, DIL, DEA, DL). La interfaz incluye accesibilidad DUA (modo nocturno + filtro de luz cálida ajustable) y autenticación diferenciada para estudiantes y docentes.

> **Tesis de pregrado** — Ingeniería Civil Informática, Universidad de Playa Ancha
> **Tesista**: Heidrium Nauj Aguirre Andrades
> **Profesor guía**: Dr. Franklin Johnson
> **Versión del prototipo**: técnica-operativa (julio 2026)

---

## Stack tecnológico

| Capa | Tecnología | Propósito |
|---|---|---|
| Frontend | Streamlit 1.58 sobre python:3.11-slim | Interfaz de chat + panel docente con sidebar DUA |
| HTTPS local | Cert autofirmado con mkcert | Requisito para `getUserMedia()` (micrófono) |
| LLM | Google Gemini 2.5 Flash (texto + audio multimodal) | Tutor socrático con system prompt personalizado |
| BD relacional | MySQL 8.0 (charset utf8mb4) | 13 tablas: perfil PIE, sesiones, auditoría, intento_login |
| BD vectorial | ChromaDB 0.5.3 con HNSW | Andamiaje curricular Mineduc con embeddings |
| Driver MySQL | pymysql 1.1.1 | Conexión con reintentos y ping-reconnect |
| Resiliencia | tenacity 9.0.0 | Reintentos con backoff exponencial (microcortes) |
| Autenticación | bcrypt 4.2.0 (rounds=12) | Hash de contraseñas docentes con rate limit 5/15min |
| STT / voz | streamlit-mic-recorder → Gemini multimodal | Captura de audio del estudiante y transcripción |
| Config | python-dotenv 1.0.1 | Carga de `.env` y variables de entorno |
| Ingesta PDFs | langchain-community + pypdf | Pipeline de carga de Mineduc a ChromaDB |
| Accesibilidad DUA | CSS/JS inyectado + slider 0-100% | Modo nocturno + filtro de luz cálida persistente |
| Personalización | REGLAS_POR_DIAGNOSTICO en `core/personalizacion.py` | Adaptación pedagógica por código PIE |
| Orquestación | Docker + Docker Compose (red bridge, named volumes, healthcheck) | 2 servicios: `db_relacional` y `app_tutor` |
| Tests | pytest 9.1.1 (45 tests pasando) | Unit tests de auth, admin, prompts, DUA, personalización |

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                       Colegio Murialdo                          │
│  (apoderado / docente PIE / coordinadora PIE)                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │ navegador Chrome/Edge
                          │ HTTPS (cert autofirmado mkcert)
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│          app_tutor (Docker container, Streamlit)               │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  app.py (sidebar + chat + panel docente con tabs)      │     │
│  │  core/auth.py (login dual: correo / bcrypt+rate)      │     │
│  │  core/admin.py (CRUD estudiante, badges de sesion)    │     │
│  │  core/dua.py (modo nocturno + slider filtro 0-100%)   │     │
│  │  core/personalizacion.py (reglas TEA/TDAH/DIL/...)   │     │
│  │  core/prompts.py (system instruction socratico)        │     │
│  │  core/retries.py (tenacity + ping-reconnect)         │     │
│  └──────────────────┬─────────────────────────────────────┘     │
│                     │ @st.cache_resource (conexiones)          │
│                     │ @st.cache_data (perfil PIE, TTL 5min)    │
│                     │  ┌────────────────────────────┐         │
│                     │  │ Gemini 2.5 Flash (texto+voz)│         │
│                     │  └────────────────────────────┘         │
└─────┬───────────────────────┬────────────────────────────────────┘
      │ red bridge            │ red bridge
      ▼                       ▼
┌────────────────┐    ┌────────────────────────────────────┐
│  db_relacional │    │  ChromaDB (volumen chroma_data)     │
│  (MySQL 8)     │    │  Embeddings Mineduc + historial     │
│  13 tablas     │    │  (texto transcrito de audio)         │
│  volumen       │    └────────────────────────────────────┘
│  mysql_data    │
└────────────────┘
```

**Flujo del tutor socrático** (cada turno del chat):

1. El usuario escribe o habla (micrófono).
2. `core/auth.py` carga su perfil PIE desde MySQL (nombre, curso, nivel, diagnóstico).
3. `core/llm.py:buscar_andamiaje_curricular` recupera chunks relevantes de ChromaDB.
4. `core/personalizacion.py:reglas_por_diagnostico` añade el bloque pedagógico específico del diagnóstico.
5. `core/prompts.py:system_instruction_socratico` arma el system prompt con todo lo anterior.
6. `Gemini 2.5 Flash` responde siguiendo el método socrático, **sin dar la respuesta directa**.
7. `core/retries.py` asegura resiliencia ante microcortes de red.

---

## Caracterización pedagógica PIE

El tutor **adapta su comportamiento en función del diagnóstico PIE del estudiante** mediante reglas explícitas, no mediante inferencia del LLM. Esto elimina la dependencia del conocimiento general del modelo sobre cada condición del neurodesarrollo.

| Diagnóstico | Adaptaciones del tutor (resumen) |
|---|---|
| **TEA** | Lenguaje literal y predecible. Sin ironía, metáforas, sarcasmo ni dobles sentidos. Pasos numerados. Consistencia léxica (mismas palabras para repetir). Anuncia transiciones. No bromas. |
| **TDAH** | Respuestas cortas (3-5 líneas). Anclajes visuales (emojis, separadores). Refuerzo positivo cada 1-2 pasos. Redirige sin regañar. Ofrece descanso si frustra. |
| **DIL** | Vocabulario concreto. Repite consignas con otras palabras. Desglosa problemas en sub-pasos. Ejemplos antes de abstracción. |
| **DEA** | Identifica canal (lectura/escritura/cálculo). Dislexia: leer en voz alta, no penalizar ortografía. Discalculia: material concreto antes de números. |
| **DL** | Palabras simples, sinónimos fáciles ("juntar" en vez de "sumar"). Ejemplos visuales. Validación corta ("Muy bien!"). Repite la pregunta si no entendió. |

**Importante**: el alumno **nunca ve su diagnóstico** en la interfaz. La personalización es invisible para él pero observable para el docente en la respuesta del tutor.

---

## Estructura del repositorio

```
its_rag_math/
├── app.py                              # Frontend Streamlit (sidebar, login, chat, panel)
├── main.py                             # CLI de prueba del flujo completo
├── ingest_pipeline.py                  # Carga PDFs Mineduc a MySQL + ChromaDB
├── Dockerfile                          # Imagen python:3.11-slim + libgomp1 + appuser no-root
├── docker-compose.yml                  # 2 servicios: db_relacional + app_tutor
├── requirements.txt                    # Dependencias pinneadas
├── pyproject.toml                      # Metadata del proyecto (Python 3.11)
├── uv.lock                             # Lockfile reproducible
│
├── core/                               # Núcleo modular de la app
│   ├── __init__.py
│   ├── config.py                       # Carga .env + variables de entorno
│   ├── auth.py                         # Login dual: SesionEstudiante + SesionDocente
│   ├── admin.py                        # CRUD estudiante_pie + SesionTutoria + badges
│   ├── dua.py                          # DARK_CSS + slider 0-100% + persistencia JSON
│   ├── personalizacion.py              # REGLAS_POR_DIAGNOSTICO (5 perfiles PIE)
│   ├── prompts.py                      # system_instruction_socratico
│   ├── llm.py                          # Helpers LLM (ventana, parseo multimodal)
│   └── retries.py                      # Conexión MySQL con tenacity
│
├── database/
│   ├── connection.py                   # Conexión SQLAlchemy (legacy)
│   ├── seed.py                         # 1 docente + 3 estudiantes seed
│   └── reparar_estudiantes_bug.py      # Script idempotente de reparacion
│
├── data/
│   ├── schema.sql                      # DDL completo (13 tablas + seed inicial)
│   ├── mineduc_pdfs/                   # 16 PDFs del Mineduc (1B a 4B)
│   └── assets/                         # Logos y avatares del frontend
│
├── .streamlit/
│   └── config.toml                     # Configuracion de Streamlit (puerto, SSL)
│
├── docs/                               # Documentacion institucional del piloto
│   ├── Carta_Gantt_2do_Semestre_2026.pdf
│   ├── Carta_Gantt_2do_Semestre_2026.docx
│   ├── CONTRATO_CONFIDENCIALIDAD_DATOS.md
│   ├── CONTRATO_CONFIDENCIALIDAD_DATOS.docx
│   ├── AUTORIZACION_TRATAMIENTO_DATOS.md
│   ├── AUTORIZACION_TRATAMIENTO_DATOS.docx
│   ├── CORREO_INSTITUCIONAL_2DO_SEMESTRE.md
│   ├── MANUAL_DOCENTE_PIE.md
│   ├── PLANTILLA_INGESTA_ESTUDIANTES.csv
│   ├── certificados-tls.md
│   ├── build_contrato_docx.py
│   ├── build_autorizacion_docx.py
│   └── assets/
│       └── logo_upa.png
│
├── Informe/                            # Documento de tesis
│   ├── Tesis_HeidriumAguirre_v2.docx
│   ├── Tesis_HeidriumAguirre_v3.docx
│   ├── Tesis_HeidriumAguirre_v2.backup_*.docx
│   └── diff_v2_v3.md
│
├── tests/                              # 45 tests pytest pasando
│   ├── test_admin.py
│   ├── test_app_helpers.py
│   ├── test_auth.py
│   ├── test_auth_query.py
│   ├── test_config.py
│   ├── test_crear_estudiante.py
│   ├── test_dua.py
│   ├── test_personalizacion.py
│   └── test_prompts.py
│
├── .env                                # Variables de entorno (NO versionado)
├── .env.example                        # Plantilla de .env
├── .gitignore
├── .dockerignore
└── README.md                           # Este archivo
```

---

## Quickstart

### Prerrequisitos
- Python 3.11
- Docker Desktop + Docker Compose
- `mkcert` (para certs TLS locales)
- (Opcional) `uv` para manejo del entorno virtual

### 1. Clonar y configurar variables de entorno

```bash
git clone https://github.com/HeidriumAguirre/Proyecto_Tesis.git
cd Proyecto_Tesis
cp .env.example .env
# Editar .env y rellenar GEMINI_API_KEY (obtener en https://aistudio.google.com/app/apikey)
```

### 2. Generar certs TLS autofirmados

```bash
mkcert -install
mkdir -p docker/certs
mkcert -cert-file docker/certs/server.crt \
       -key-file docker/certs/server.key \
       localhost 127.0.0.1
```

Detalle completo en [`docs/certificados-tls.md`](docs/certificados-tls.md).

### 3. Levantar con Docker Compose

```bash
docker compose up --build
```

- MySQL en `db_relacional` queda healthy.
- Streamlit arranca en `https://localhost:8501`.
- Acepta el cert autofirmado la primera vez en el navegador.

**Credenciales seed** (si no has ejecutado el seed manualmente):
- Docente: `heidrium.aguirre@murialdo.cl` / `Demo2026!`
- Estudiante: `mateo.gonzalez@murialdo.cl` (sin contraseña)

### 4. (Opcional) Sembrar datos de prueba

Si el contenedor MySQL arrancó con la BD vacía (no se cargó el `schema.sql` automáticamente porque el volumen ya existía), ejecuta:

```bash
docker compose exec app_tutor python database/seed.py
```

### 5. Setup para desarrollo local (sin Docker)

```bash
uv venv .venv --python 3.11
uv pip install -r requirements.txt

# Levantar MySQL por separado (Workbench o Docker solo MySQL)
# y apuntar MYSQL_HOST en .env a localhost

# Correr tests
.venv/bin/pytest tests/ -v

# Correr la app
.venv/bin/streamlit run app.py
```

---

## Uso

### Login dual (sidebar)

| Pestaña | Usuario | Credenciales |
|---|---|---|
| 👤 Estudiante / Persona de apoyo | Alumno PIE | Solo correo académico (pre-creado por el docente) |
| 🧑‍🏫 Docente PIE | Educador PIE | Correo + contraseña (bcrypt) |

### Como estudiante

1. Login con tu correo académico.
2. Escribe con el teclado o usa el botón 🎤 para hablar.
3. El Tutor Socrático (Gemini 2.5 Flash) responde **guiando con preguntas**, sin dar el resultado.
4. Cada respuesta tiene un botón 🔊 para escucharla en voz alta (TTS del navegador).
5. Tus mensajes y los del tutor quedan registrados en `historial_interaccion` para análisis posterior.

### Como docente PIE

1. Login con tu correo y contraseña.
2. **Sidebar**: activa/desactiva el 🌙 Modo Nocturno y ajusta el slider 🔅 Filtro de Luz Nocturna (0-100%). Tus preferencias se guardan automáticamente.
3. **Pestañas por nivel** (1° a 4° Básico) con selector A/B para subdivisión.
4. **Por cada alumno**:
   - Ver perfil completo (nombre, adaptación, pictórico).
   - ✏️ Editar (abre formulario inline).
   - 🗑️ Eliminar (soft delete: preserva historial).
   - ➕ Agregar nuevo alumno (formulario con RUT anonimizado, diagnóstico, etc.).
5. **Panel de sesiones recientes** con badges de color:
   - 🟡 **Activa** (en uso ahora)
   - 🟢 **Completada** (cerrada o >30 min sin actividad)
   - 🔴 **Abandonada** (cerrada manualmente como abandonada)
6. Acciones sobre sesiones activas: ✅ Cerrar / 🔴 Abandonar.

### Accesibilidad DUA (sidebar)

- **🌙 Modo Nocturno**: tema oscuro completo (texto blanco sobre fondo cálido, scrollbar custom, focus rings azules, hover states claros).
- **🔅 Filtro de Luz Nocturna** (slider 0-100%): aplica `sepia()` + `hue-rotate()` + `saturate()` escalado. Recomendado 0-30% diurno, 50-70% vespertino, 80-100% para TEA/TDAH con sensibilidad sensorial.

---

## Documentación institucional (piloto 2do semestre 2026)

Adjuntos enviados al Colegio San Leonardo Murialdo en el correo de coordinación:

| Documento | Formato | Para qué |
|---|---|---|
| `Carta_Gantt_2do_Semestre_2026.pdf` | PDF | Cronograma de 5 fases (F1-F5) + 6 hitos |
| `CONTRATO_CONFIDENCIALIDAD_DATOS.docx` | Word | Documento **descriptivo** para mostrar en reuniones. No se firma. |
| `AUTORIZACION_TRATAMIENTO_DATOS.docx` | Word | Documento **firmable** por colegio, coordinadora PIE y apoderado/a |
| `MANUAL_DOCENTE_PIE.md` | Markdown | Guía rápida de 2 páginas para el educador PIE |
| `PLANTILLA_INGESTA_ESTUDIANTES.csv` | CSV | Plantilla de 4 alumnos anonimizados para ingesta |

Y la **tesis**:
- [`Informe/Tesis_HeidriumAguirre_v3.docx`](Informe/Tesis_HeidriumAguirre_v3.docx) — manuscrito sincronizado con el código
- [`Informe/diff_v2_v3.md`](Informe/diff_v2_v3.md) — auditoría de cambios v2→v3

---

## Seguridad y cumplimiento

| Medida | Implementación |
|---|---|
| API Key fuera del repo | Variable `GEMINI_API_KEY` en `.env` (excluido por `.gitignore`) |
| Certs TLS fuera del repo | `docker/certs/*.crt/*.key` excluidos |
| Hash de contraseñas | bcrypt rounds=12 en `core/auth.py` |
| Rate limit login | Tabla `intento_login`: máx 5 intentos fallidos en 15 min por correo |
| Trazabilidad PIE | Tabla `auditoria_docente` registra toda acción del docente (crear, editar, eliminar, cerrar/abandonar sesión) |
| Soft delete | Columnas `deleted_at` en `usuario` y `estudiante_pie`. Preserva historial. |
| HTTPS obligatorio | Streamlit expone sobre HTTPS con cert autofirmado. Requisito para `getUserMedia()` (micrófono). |
| Aislamiento de contenedor | Usuario no-root `appuser`, dependencias mínimas (`libgomp1` para ChromaDB) |
| Cifrado en tránsito | Certs TLS + Streamlit forzado a HTTPS en `Dockerfile` |
| Cumplimiento normativo | Ley 19.628 (Protección de Datos), DS 170/2009 (PIE), DE 83/2015 (adecuación curricular) |

### Privacidad del estudiante

El alumno **nunca ve su diagnóstico PIE** en la interfaz. La personalización es invisible para él. La única información personal visible es su nombre, curso y subdivisión.

---

## Tests

```bash
.venv/bin/pytest tests/ -v
```

**Cobertura actual**: 45/45 tests pasando.

Módulos cubiertos:
- `test_admin.py`: CRUD + SesionTutoria + badges
- `test_app_helpers.py`: ventana deslizante + parseo multimodal
- `test_auth.py`: bcrypt + rate limit
- `test_auth_query.py`: regresión `only_full_group_by` + no GROUP BY en auth
- `test_config.py`: carga de `.env`
- `test_crear_estudiante.py`: regresión bug de alineación de parámetros
- `test_dua.py`: slider + persistencia + legacy bool→pct
- `test_personalizacion.py`: 5 diagnósticos + palabras clave + fallback
- `test_prompts.py`: integración REGLAS_POR_DIAGNOSTICO con system prompt

---

## Roadmap 2do semestre 2026 (piloto)

Carta Gantt de 5 fases (agosto – diciembre 2026):

| Fase | Actividad | Mes |
|---|---|---|
| F1 — Coordinación | Reunión kickoff + consentimientos | Ago-Sep |
| F2 — Datos | Ingesta CSV anonimizado (4 alumnos, 1 por nivel) | Sep-Oct |
| F3 — Pasantía | Observación no participante en aulas | Oct-Nov |
| F4 — Demos | 3 reuniones presenciales con docentes y estudiantes | Nov |
| F5 — Cierre | Tesis v4 con resultados + preparación defensa | Dic |

**Alcance del piloto**: 4 alumnos mínimo (1 por nivel: 1° a 4° Básico), idealmente con diagnósticos PIE distintos. Si más apoderados se suman voluntariamente, el alcance se amplía.

Detalle completo en [`docs/Carta_Gantt_2do_Semestre_2026.pdf`](docs/Carta_Gantt_2do_Semestre_2026.pdf).

---

## Contribuciones y contacto

**Heidrium Nauj Aguirre Andrades**
Ingeniería Civil Informática
Universidad de Playa Ancha
Correo institucional: `heidrium.aguirre@alumnos.upla.cl`

Dirigida por: **Dr. Franklin Johnson** — Profesor Guía, Universidad de Playa Ancha.

---

## Licencia

Tesis académica de pregrado — Universidad de Playa Ancha, 2026.
Uso educativo y de investigación. No comercial.
