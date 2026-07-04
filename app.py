"""
ITS RAG Math - Colegio Murialdo Valparaiso
Sistema de Tutoria Inteligente inclusivo para estudiantes PIE.

Punto de entrada Streamlit. Arquitectura:
- MySQL relacional (perfil PIE, historial de sesion, usuario, docentes, auditoria).
- ChromaDB vectorial (andamiaje curricular Mineduc).
- Gemini 2.5 Flash multimodal (texto + audio).
- Entrada por teclado Y por voz (streamlit-mic-recorder).
- Login dual: estudiante (correo) y docente (correo + bcrypt).
- Panel docente con CRUD y badges de color por estado de sesion.
- Toggles DUA (modo nocturno + filtro de luz) con persistencia en BD.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import uuid

import pymysql
import streamlit as st
import streamlit.components.v1 as html_visual
from google import genai
from PIL import Image
from streamlit_mic_recorder import mic_recorder

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.admin import (  # noqa: E402
    CURSOS_VALIDOS,
    NIVELES_ADAPTACION,
    SUBDIVISIONES_VALIDAS,
    SesionTutoria,
    actualizar_estudiante,
    badge_html,
    cerrar_sesion_como_completada,
    crear_estudiante,
    listar_diagnosticos,
    listar_estudiantes_por_curso,
    listar_sesiones_de_curso,
    marcar_sesion_abandonada,
    obtener_diagnosticos_de_estudiante,
    obtener_estudiante_por_id,
    sesiones_activas_por_estudiante,
    set_diagnosticos_de_estudiante,
    soft_delete_estudiante,
)
from core.auth import (  # noqa: E402
    SesionDocente,
    SesionEstudiante,
    autenticar_docente,
    autenticar_estudiante,
    cerrar_sesion,
    registrar_auditoria,
)
from core.config import (  # noqa: E402
    GEMINI_API_KEY,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)
from core.dua import (  # noqa: E402
    PreferenciasDUA,
    aplicar_estilos,
    cargar_preferencias,
    guardar_preferencias,
    render_toggles,
)
from core.llm import (  # noqa: E402
    construir_contexto_ventana,
    separar_transcripcion_y_respuesta,
)
from core.prompts import system_instruction_socratico  # noqa: E402
from core.retries import (  # noqa: E402
    asegurar_conexion_viva,
    conectar_con_reintentos,
    ejecutar_query_segura,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("its_rag_math")

# ============================================================================
# A. RECURSOS CACHEADOS
# ============================================================================

@st.cache_resource(show_spinner="Conectando a MySQL...")
def obtener_conexion_mysql() -> pymysql.connections.Connection:
    return conectar_con_reintentos(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DATABASE,
    )


@st.cache_resource(show_spinner="Cargando indice vectorial...")
def obtener_cliente_chroma():
    import chromadb
    chroma = chromadb.PersistentClient(path="./chroma_db")
    return chroma.get_or_create_collection(name="mineduc_matematica")


@st.cache_resource(show_spinner="Inicializando cliente Gemini...")
def obtener_cliente_gemini():
    return genai.Client(api_key=GEMINI_API_KEY)


try:
    db_connection = obtener_conexion_mysql()
    vector_collection = obtener_cliente_chroma()
    ai_client = obtener_cliente_gemini()
except Exception as e:
    st.error(f"Error critico en capa de inicializacion: {e}")
    logger.exception("Fallo en inicializacion")
    st.stop()


# ============================================================================
# B. CAPA DE DATOS (RAG, sesion, historial)
# ============================================================================

def buscar_andamiaje_curricular(consulta: str, curso: str, tipo_doc: str) -> str:
    try:
        resultados = vector_collection.query(
            query_texts=[consulta], n_results=3,
            where={"$and": [{"curso": curso}, {"tipo": tipo_doc}]},
        )
        documentos = resultados.get("documents", [[]])[0]
        return "\n".join(documentos) if documentos else ""
    except Exception:
        logger.exception("Error consultando ChromaDB")
        return ""


def cargar_mensajes_anteriores(id_sesion: str) -> list[dict]:
    sql = """
        SELECT remitente, contenido_mensaje
        FROM historial_interaccion
        WHERE id_sesion = %s
        ORDER BY fecha_envio ASC
    """
    try:
        registros = ejecutar_query_segura(db_connection, sql, (id_sesion,), fetch="all") or []
    except Exception:
        logger.exception("Error cargando historial desde MySQL")
        return []
    mensajes: list[dict] = []
    for reg in registros:
        role = "user" if reg["remitente"] == "Estudiante" else "assistant"
        mensajes.append({"role": role, "content": reg["contenido_mensaje"]})
    return mensajes


def guardar_mensaje_en_historial(
    id_sesion: str, remitente: str, contenido_mensaje: str, id_recurso: str | None = None
) -> None:
    sql = """
        INSERT INTO historial_interaccion (id_sesion, id_recurso, remitente, contenido_mensaje)
        VALUES (%s, %s, %s, %s)
    """
    try:
        ejecutar_query_segura(
            db_connection, sql,
            (id_sesion, id_recurso, remitente, contenido_mensaje),
            fetch="none",
        )
    except Exception:
        logger.exception("Error al persistir interaccion en MySQL")


def crear_sesion_tutoria(
    id_estudiante: str, id_oa: str, id_usuario: str | None = None,
    curso_subdivision: str | None = None,
) -> str:
    id_sesion = str(uuid.uuid4())
    sql = """
        INSERT INTO sesion_tutoria
            (id_sesion, id_estudiante, id_usuario, id_oa, curso_subdivision,
             estado_emocional_inicial, estado_sesion)
        VALUES (%s, %s, %s, %s, %s, 'Neutro', 'Activa')
    """
    ejecutar_query_segura(
        db_connection, sql,
        (id_sesion, id_estudiante, id_usuario, id_oa, curso_subdivision),
        fetch="none",
    )
    return id_sesion


def obtener_oa_por_curso(conn, curso: str) -> dict | None:
    sql = """
        SELECT id_oa, codigo, descripcion
        FROM objetivo_aprendizaje
        WHERE nivel_curso = %s
        ORDER BY codigo ASC LIMIT 1
    """
    try:
        return ejecutar_query_segura(conn, sql, (curso,), fetch="one")
    except Exception:
        return None


# ============================================================================
# C. LLAMADAS AL LLM
# ============================================================================

def llamar_gemini_texto(system_instruction: str, conversacion: str) -> str:
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=conversacion,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_instruction, temperature=0.3,
        ),
    )
    return response.text


def llamar_gemini_audio(system_instruction: str, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    import base64
    parte_audio = {
        "inline_data": {
            "mime_type": mime_type,
            "data": base64.b64encode(audio_bytes).decode("ascii"),
        }
    }
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            parte_audio,
            "Transcribe el audio del estudiante y luego responde como tutor socratico.",
        ],
        config=genai.types.GenerateContentConfig(
            system_instruction=system_instruction, temperature=0.3,
        ),
    )
    return response.text


# ============================================================================
# D. ASSETS Y PAGE CONFIG
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_insignia = os.path.join(BASE_DIR, "data", "assets", "insignia_principal.png")
ruta_icono = os.path.join(BASE_DIR, "data", "assets", "icono_murialdo.png")
ruta_avatar_socrates = os.path.join(BASE_DIR, "data", "assets", "socrates.png")

try:
    insignia_img = Image.open(ruta_insignia)
    icono_img = Image.open(ruta_icono)
except FileNotFoundError as e:
    st.error(f"No se encontro un asset requerido: {e}")
    st.stop()

st.set_page_config(
    page_title="ITS - Colegio Murialdo Valparaiso",
    page_icon=icono_img, layout="centered",
)

# CSS base (la parte DUA se sobreescribe despues segun preferencias)
st.markdown(
    """
    <style>
    .stApp, div[data-testid="stChatMessageContainer"] {
        background-color: #FFFFFF !important;
    }
    p, span, label, li {
        color: #111111 !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    }
    .header-title-murialdo {
        color: #0F2C59 !important; font-size: 32px; font-weight: 700;
        letter-spacing: -1px; text-align: center; margin-top: -15px;
        text-transform: uppercase; font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    .header-subtitle-murialdo {
        color: #555555 !important; font-size: 16px; font-weight: 400;
        text-align: center; margin-top: -10px; margin-bottom: 20px;
    }
    .perfil-card-estudiante {
        background-color: #FFFFFF !important;
        border-top: 4px solid #FFD700 !important;
        border-left: 1px solid #E1E8ED !important;
        border-right: 1px solid #E1E8ED !important;
        border-bottom: 1px solid #E1E8ED !important;
        padding: 18px; border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 25px;
    }
    div[data-testid="stChatMessage"] {
        background-color: #F8F9FA; border-radius: 8px; margin-bottom: 10px;
        border: 1px solid #EEEEEE;
    }
    div[data-testid="stChatMessageAssistant"] {
        background-color: #FFFFFF !important;
        border-left: 6px solid #0F2C59;
    }
    .transcripcion-box {
        background-color: #E8F0FE; border-left: 3px solid #1A73E8;
        padding: 8px 12px; margin: 4px 0 8px 0; border-radius: 4px;
        font-size: 13px; color: #174EA6 !important; font-style: italic;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# E. SIDEBAR
# ============================================================================

def render_login_screen() -> None:
    """Pantalla inicial cuando no hay sesion activa."""
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.image(insignia_img, width=110)
    with col_titulo:
        st.markdown(
            "<div class='header-title-murialdo'>COLEGIO MURIALDO VALPARAISO</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='header-subtitle-murialdo'>"
            "Plataforma RAG de Acompanamiento Matematico Inclusivo"
            "</div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")

    tab_est, tab_doc = st.tabs(["👤 Estudiante / Persona de apoyo", "🧑‍🏫 Docente PIE"])

    with tab_est:
        st.markdown("Ingresa tu **correo academico institucional**. No necesitas contrasena.")
        with st.form("form_login_est", clear_on_submit=False):
            correo = st.text_input(
                "Correo academico", placeholder="mateo.gonzalez@murialdo.cl"
            ).strip().lower()
            submitted = st.form_submit_button("Ingresar", use_container_width=True)
        if submitted:
            if not correo:
                st.error("Ingresa tu correo academico.")
            else:
                sesion = autenticar_estudiante(db_connection, correo)
                if sesion:
                    st.session_state.tipo_usuario = "estudiante"
                    st.session_state.estudiante = sesion
                    st.session_state.id_sesion_tutoria = None
                    st.session_state.messages = []
                    st.success(f"Bienvenido, {sesion.nombre_completo}!")
                    st.rerun()
                else:
                    st.error(
                        "Tu correo no esta registrado. Pide a tu docente PIE "
                        "que cree tu perfil."
                    )

    with tab_doc:
        st.markdown("Acceso para docentes. Ingresa tu correo y contrasena.")
        with st.form("form_login_doc", clear_on_submit=False):
            correo = st.text_input("Correo", placeholder="heidrium.aguirre@murialdo.cl").strip().lower()
            password = st.text_input("Contrasena", type="password")
            submitted = st.form_submit_button("Ingresar", use_container_width=True)
        if submitted:
            if not correo or not password:
                st.error("Completa correo y contrasena.")
            else:
                sesion, err = autenticar_docente(db_connection, correo, password)
                if sesion:
                    st.session_state.tipo_usuario = "docente"
                    st.session_state.docente = sesion
                    st.success(f"Bienvenida, {sesion.nombre_completo}!")
                    st.rerun()
                else:
                    st.error(err or "No se pudo iniciar sesion.")


def render_sidebar_auth_block() -> None:
    """Bloque de sesion activa + logout en el sidebar."""
    tipo = st.session_state.get("tipo_usuario")
    st.markdown("---")
    st.markdown("##### Sesion actual")

    if tipo == "estudiante":
        s: SesionEstudiante = st.session_state.estudiante
        st.markdown(f"**{s.nombre_completo}**")
        st.caption(f"📚 {s.curso.replace('_', ' ')} Basicos" + (f" {s.curso_subdivision}" if s.curso_subdivision else ""))
        if st.button("🚪 Cerrar sesion", use_container_width=True):
            cerrar_sesion()
            st.rerun()
    elif tipo == "docente":
        d: SesionDocente = st.session_state.docente
        st.markdown(f"**{d.nombre_completo}**")
        st.caption(f"🧑‍🏫 {d.rol}")
        if st.button("🚪 Cerrar sesion", use_container_width=True):
            cerrar_sesion()
            st.rerun()


def render_sidebar_dua_block() -> None:
    """Toggles DUA: cargan de BD al iniciar, persisten al cambiar."""
    st.markdown("---")
    st.markdown("##### 🎨 Accesibilidad DUA")
    prefs_actuales = render_toggles(key_prefix="dua")
    nueva = prefs_actuales
    # Comparar contra ultima persistencia
    ultima = st.session_state.get("_dua_ultimo_json")
    nuevo_json = nueva.to_json()
    if nuevo_json != ultima:
        # Persistir segun tipo de usuario
        if st.session_state.get("tipo_usuario") == "docente":
            d: SesionDocente = st.session_state.docente
            guardar_preferencias(db_connection, "usuario", "id_usuario", d.id_usuario, nueva)
        elif st.session_state.get("tipo_usuario") == "estudiante":
            s: SesionEstudiante = st.session_state.estudiante
            guardar_preferencias(db_connection, "estudiante_pie", "id_estudiante", s.id_estudiante, nueva)
        st.session_state["_dua_ultimo_json"] = nuevo_json


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 🏫 Colegio Murialdo")
        st.caption("ITS - Tutoria Inteligente Inclusiva")

        # Toggles DUA solo si esta logueado
        if st.session_state.get("tipo_usuario"):
            render_sidebar_dua_block()
            render_sidebar_auth_block()
        else:
            st.info("👈 Inicia sesion para acceder.")


# ============================================================================
# F. CHAT DEL ESTUDIANTE
# ============================================================================

def _nombre_corto(s: SesionEstudiante) -> str:
    partes = s.nombre_completo.split()
    if len(partes) >= 3:
        return f"{partes[0]} {partes[2]}"
    return s.nombre_completo


def _init_sesion_activa(estudiante: SesionEstudiante) -> str:
    """Crea o recupera la sesion Activa del estudiante (politica: 1 activa)."""
    if st.session_state.get("id_sesion_tutoria"):
        return st.session_state.id_sesion_tutoria

    activas = sesiones_activas_por_estudiante(db_connection, estudiante.id_estudiante)
    if activas:
        st.session_state.id_sesion_tutoria = activas[0].id_sesion
        return activas[0].id_sesion

    oa = obtener_oa_por_curso(db_connection, estudiante.curso)
    if not oa:
        st.warning("No hay objetivos de aprendizaje configurados para este curso.")
        st.stop()
    id_sesion = crear_sesion_tutoria(
        id_estudiante=estudiante.id_estudiante,
        id_oa=oa["id_oa"],
        id_usuario=estudiante.id_usuario,
        curso_subdivision=estudiante.curso_subdivision,
    )
    st.session_state.id_sesion_tutoria = id_sesion
    return id_sesion


def render_boton_escuchar(texto: str, key: str) -> None:
    texto_json = json.dumps(texto)
    html_visual.html(
        f"""
        <script>
        function hablar_{key}() {{
            window.speechSynthesis.cancel();
            const textoOriginal = {texto_json};
            const textoLimpio = textoOriginal
                .replace(/[\\\\*#\\-_`]/g, "")
                .replace(/[\\u{{1F300}}-\\u{{1FAFF}}\\u{{2600}}-\\u{{27BF}}]/gu, "")
                .replace(/\\s+/g, " ").trim() || textoOriginal;
            const u = new SpeechSynthesisUtterance(textoLimpio);
            u.lang = 'es-CL'; u.rate = 0.95;
            window.speechSynthesis.speak(u);
        }}
        </script>
        <button onclick="hablar_{key}()" style="
            background-color: #0F2C59; color: white; border: none;
            padding: 8px 16px; border-radius: 20px; cursor: pointer;
            font-size: 13px; font-weight: bold; font-family: sans-serif;
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);">Escuchar a Socrates</button>
        """,
        height=45,
    )


def render_chat_estudiante(estudiante: SesionEstudiante) -> None:
    nombre_corto = _nombre_corto(estudiante)
    id_sesion = _init_sesion_activa(estudiante)

    # Cabecera del chat
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.image(insignia_img, width=110)
    with col_titulo:
        st.markdown(
            "<div class='header-title-murialdo'>COLEGIO MURIALDO VALPARAISO</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='header-subtitle-murialdo'>"
            "Plataforma RAG de Acompanamiento Matematico Inclusivo"
            "</div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")

    # Perfil (PRIVACIDAD: solo nombre + curso, sin diagnostico)
    subdivision_txt = f" {estudiante.curso_subdivision}" if estudiante.curso_subdivision else ""
    st.markdown(
        f"""
        <div class='perfil-card-estudiante'>
            <div style='color: #0F2C59; font-size: 18px; font-weight: 700; margin-bottom: 8px;'>
                Mi Panel de Matematicas
            </div>
            <div style='font-size: 15px; color: #444444; line-height: 1.6;'>
                <b>Estudiante:</b> {nombre_corto}<br>
                <b>Curso:</b> {estudiante.curso.replace('_', ' ')} Basicos{subdivision_txt}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Cargar historial
    if "messages" not in st.session_state:
        st.session_state.messages = cargar_mensajes_anteriores(id_sesion)

    # Render del historial
    for i, msg in enumerate(st.session_state.messages):
        avatar = ruta_avatar_socrates if msg["role"] == "assistant" else "🙋"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                render_boton_escuchar(msg["content"], key=f"tts_{i}")

    # Boton de cerrar sesion del tutor (docente o sistema)
    if st.session_state.get("id_sesion_tutoria"):
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("Finalizar sesion", type="secondary"):
                cerrar_sesion_como_completada(db_connection, st.session_state.id_sesion_tutoria)
                st.session_state.id_sesion_tutoria = None
                st.session_state.messages = []
                st.success("Sesion finalizada.")
                st.rerun()

    # Entradas: teclado + microfono
    pregunta_texto = st.chat_input(f"Escribe tu duda, {nombre_corto.split()[0]}...")
    st.markdown("##### O habla con Socrates (microfono)")
    audio_grabado = mic_recorder(
        start_prompt="🎤 Grabar", stop_prompt="⏹️ Detener",
        just_once=False, use_container_width=True, key="mic_recorder_principal",
    )

    pregunta_usuario: str | None = pregunta_texto
    transcripcion_audio: str | None = None
    es_input_voz = False

    if audio_grabado and audio_grabado.get("bytes"):
        es_input_voz = True
        with st.spinner("🎙️ Procesando audio..."):
            try:
                contexto_mineduc = buscar_andamiaje_curricular(
                    consulta="consulta hablada del estudiante",
                    curso=estudiante.curso, tipo_doc="Guia_Docente",
                )
                system_inst = system_instruction_socratico(
                    nombre=nombre_corto,
                    diagnosticos=estudiante.diagnosticos or "",
                    nivel_adaptacion=estudiante.nivel_adaptacion_lenguaje,
                    requiere_apoyo_pictorico=estudiante.requiere_apoyo_pictorico,
                    contexto_pedagogico=contexto_mineduc,
                )
                resultado_llm = llamar_gemini_audio(
                    system_inst, audio_grabado["bytes"], mime_type="audio/wav",
                )
                transcripcion_audio, pregunta_usuario = separar_transcripcion_y_respuesta(resultado_llm)
                if not pregunta_usuario:
                    pregunta_usuario = transcripcion_audio or "(no se pudo transcribir)"
            except Exception as e:
                st.error(f"Error al procesar audio: {e}")
                logger.exception("Error en pipeline de audio")
                pregunta_usuario = None

    if pregunta_usuario:
        if es_input_voz and transcripcion_audio:
            st.markdown(
                f"<div class='transcripcion-box'>🗣️ <b>Escuchado:</b> {transcripcion_audio}</div>",
                unsafe_allow_html=True,
            )

        with st.chat_message("user", avatar="🙋"):
            st.markdown(pregunta_usuario)

        st.session_state.messages.append({"role": "user", "content": pregunta_usuario})
        guardar_mensaje_en_historial(
            id_sesion=id_sesion, remitente="Estudiante", contenido_mensaje=pregunta_usuario,
        )

        with st.spinner("✨ Consultando el libro oficial del Mineduc..."):
            try:
                contexto_mineduc = buscar_andamiaje_curricular(
                    pregunta_usuario, estudiante.curso, "Guia_Docente",
                )
                system_inst = system_instruction_socratico(
                    nombre=nombre_corto,
                    diagnosticos=estudiante.diagnosticos or "",
                    nivel_adaptacion=estudiante.nivel_adaptacion_lenguaje,
                    requiere_apoyo_pictorico=estudiante.requiere_apoyo_pictorico,
                    contexto_pedagogico=contexto_mineduc,
                )
                conversacion = construir_contexto_ventana(st.session_state.messages)
                respuesta_tutor = llamar_gemini_texto(system_inst, conversacion)

                st.session_state.messages.append({"role": "assistant", "content": respuesta_tutor})
                guardar_mensaje_en_historial(
                    id_sesion=id_sesion, remitente="Tutor_IA",
                    contenido_mensaje=respuesta_tutor,
                )
            except Exception as e:
                st.error(f"Error GenAI: {e}")
                logger.exception("Error en llamada a Gemini")
                st.stop()

        st.rerun()


# ============================================================================
# G. PANEL DEL DOCENTE
# ============================================================================

def render_panel_docente(docente: SesionDocente) -> None:
    st.title("🧑‍🏫 Panel Docente PIE")
    st.caption(f"Conectado como **{docente.nombre_completo}** ({docente.rol})")

    tabs = st.tabs(["1° Básico", "2° Básico", "3° Básico", "4° Básico"])
    for tab, curso in zip(tabs, CURSOS_VALIDOS):
        with tab:
            _render_tab_curso(curso, docente)


def _render_tab_curso(curso: str, docente: SesionDocente) -> None:
    subdivision = st.radio(
        "Curso", SUBDIVISIONES_VALIDAS, horizontal=True, key=f"sub_{curso}",
    )
    st.markdown("---")

    estudiantes = listar_estudiantes_por_curso(
        db_connection, curso, subdivision, incluir_eliminados=False,
    )
    sesiones = listar_sesiones_de_curso(
        db_connection, curso, subdivision, limite=15,
    )

    col_lista, col_sesiones = st.columns([3, 2])
    with col_lista:
        st.subheader(f"👥 Alumnos de {curso.replace('_', ' ')} {subdivision}")
        if not estudiantes:
            st.info("No hay alumnos registrados en este curso.")
        else:
            for est in estudiantes:
                _render_fila_estudiante(est, docente)

        st.markdown("---")
        if st.button(f"➕ Agregar alumno a {curso} {subdivision}", use_container_width=True):
            st.session_state[f"mostrar_form_nuevo_{curso}_{subdivision}"] = True

        if st.session_state.get(f"mostrar_form_nuevo_{curso}_{subdivision}"):
            _render_form_nuevo(curso, subdivision, docente)

    with col_sesiones:
        st.subheader("📊 Sesiones recientes")
        if not sesiones:
            st.info("Sin sesiones registradas.")
        else:
            for s in sesiones:
                st.markdown(
                    f"{badge_html(s.estado_sesion)} &nbsp; `{s.id_sesion[:8]}`<br>"
                    f"<small>{s.fecha_inicio}</small>",
                    unsafe_allow_html=True,
                )
                if s.estado_sesion == "Activa":
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("✅ Cerrar", key=f"close_{s.id_sesion}"):
                            cerrar_sesion_como_completada(db_connection, s.id_sesion)
                            registrar_auditoria(
                                db_connection, docente.id_usuario, "CERRAR_SESION",
                                tabla="sesion_tutoria", id_registro=s.id_sesion,
                            )
                            st.rerun()
                    with cc2:
                        if st.button("🔴 Abandonar", key=f"aban_{s.id_sesion}"):
                            marcar_sesion_abandonada(db_connection, s.id_sesion)
                            registrar_auditoria(
                                db_connection, docente.id_usuario, "ABANDONAR_SESION",
                                tabla="sesion_tutoria", id_registro=s.id_sesion,
                            )
                            st.rerun()
                st.markdown("")


def _render_fila_estudiante(est, docente: SesionDocente) -> None:
    with st.container():
        cols = st.columns([5, 2, 1, 1])
        with cols[0]:
            st.markdown(f"**{est.nombre_completo}**  \n<small>📧 {est.correo_electronico or '—'}</small>", unsafe_allow_html=True)
        with cols[1]:
            st.caption(f"Adaptación: **{est.nivel_adaptacion_lenguaje}**")
        with cols[2]:
            if st.button("✏️", key=f"edit_{est.id_estudiante}", help="Editar"):
                st.session_state[f"editando_{est.id_estudiante}"] = True
        with cols[3]:
            if st.button("🗑️", key=f"del_{est.id_estudiante}", help="Eliminar (soft)"):
                soft_delete_estudiante(db_connection, est.id_estudiante)
                registrar_auditoria(
                    db_connection, docente.id_usuario, "SOFT_DELETE_ESTUDIANTE",
                    tabla="estudiante_pie", id_registro=est.id_estudiante,
                )
                st.rerun()
        if st.session_state.get(f"editando_{est.id_estudiante}"):
            _render_form_edicion(est, docente)
        st.divider()


def _render_form_nuevo(curso: str, subdivision: str, docente: SesionDocente) -> None:
    with st.form(f"form_nuevo_{curso}_{subdivision}", clear_on_submit=True):
        st.write(f"**Nuevo alumno en {curso} {subdivision}**")
        rut = st.text_input("RUT *", placeholder="12.345.678-9")
        nombre = st.text_input("Nombre completo *")
        correo = st.text_input("Correo academico", placeholder="nombre@murialdo.cl")
        nivel = st.selectbox("Nivel de adaptacion", NIVELES_ADAPTACION)
        pictorico = st.checkbox("Requiere apoyo pictorico", value=True)
        diags = st.multiselect(
            "Diagnosticos",
            options=[d["codigo"] for d in listar_diagnosticos(db_connection)],
            format_func=lambda c: c,
        )
        cc1, cc2 = st.columns(2)
        with cc1:
            guardar = st.form_submit_button("💾 Guardar", use_container_width=True)
        with cc2:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

    if cancelar:
        st.session_state[f"mostrar_form_nuevo_{curso}_{subdivision}"] = False
        st.rerun()

    if guardar:
        if not rut or not nombre:
            st.error("RUT y nombre son obligatorios.")
            return
        try:
            nuevo = crear_estudiante(
                db_connection,
                rut=rut, nombre_completo=nombre,
                correo_electronico=correo or None,
                curso=curso, curso_subdivision=subdivision,
                nivel_adaptacion_lenguaje=nivel,
                requiere_apoyo_pictorico=pictorico,
                id_docente=docente.id_usuario,
            )
            if diags:
                set_diagnosticos_de_estudiante(
                    db_connection, nuevo.id_estudiante, diags, docente.id_usuario,
                )
            registrar_auditoria(
                db_connection, docente.id_usuario, "CREATE_ESTUDIANTE",
                tabla="estudiante_pie", id_registro=nuevo.id_estudiante,
                detalle={"curso": curso, "subdivision": subdivision},
            )
            st.session_state[f"mostrar_form_nuevo_{curso}_{subdivision}"] = False
            st.success(f"Alumno {nombre} creado.")
            st.rerun()
        except pymysql.err.IntegrityError as e:
            if "Duplicate" in str(e):
                st.error("Ya existe un estudiante con ese RUT o correo.")
            else:
                st.error(f"Error de integridad: {e}")
        except Exception as e:
            st.error(f"Error al guardar: {e}")
            logger.exception("Error en crear_estudiante")


def _render_form_edicion(est, docente: SesionDocente) -> None:
    diags_actuales = obtener_diagnosticos_de_estudiante(db_connection, est.id_estudiante)
    diags_disponibles = [d["codigo"] for d in listar_diagnosticos(db_connection)]
    with st.form(f"form_edit_{est.id_estudiante}"):
        nombre = st.text_input("Nombre completo", value=est.nombre_completo)
        correo = st.text_input("Correo academico", value=est.correo_electronico or "")
        nivel = st.selectbox(
            "Nivel de adaptacion",
            NIVELES_ADAPTACION,
            index=NIVELES_ADAPTACION.index(est.nivel_adaptacion_lenguaje),
        )
        pictorico = st.checkbox(
            "Requiere apoyo pictorico", value=est.requiere_apoyo_pictorico,
        )
        diags = st.multiselect(
            "Diagnosticos", options=diags_disponibles, default=diags_actuales,
        )
        cc1, cc2 = st.columns(2)
        with cc1:
            guardar = st.form_submit_button("💾 Guardar cambios", use_container_width=True)
        with cc2:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

    if cancelar:
        st.session_state[f"editando_{est.id_estudiante}"] = False
        st.rerun()
    if guardar:
        try:
            actualizar_estudiante(
                db_connection,
                id_estudiante=est.id_estudiante,
                nombre_completo=nombre,
                correo_electronico=correo or None,
                curso=est.curso,
                curso_subdivision=est.curso_subdivision,
                nivel_adaptacion_lenguaje=nivel,
                requiere_apoyo_pictorico=pictorico,
            )
            set_diagnosticos_de_estudiante(
                db_connection, est.id_estudiante, diags, docente.id_usuario,
            )
            registrar_auditoria(
                db_connection, docente.id_usuario, "UPDATE_ESTUDIANTE",
                tabla="estudiante_pie", id_registro=est.id_estudiante,
            )
            st.session_state[f"editando_{est.id_estudiante}"] = False
            st.success("Cambios guardados.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
            logger.exception("Error en actualizar_estudiante")


# ============================================================================
# H. ROUTING PRINCIPAL
# ============================================================================

def main() -> None:
    tipo = st.session_state.get("tipo_usuario")
    render_sidebar()

    if tipo is None:
        render_login_screen()
        return

    # Cargar y aplicar preferencias DUA del usuario actual
    if "_dua_ultimo_json" not in st.session_state:
        if tipo == "docente":
            prefs = cargar_preferencias(
                db_connection, "usuario", "id_usuario", st.session_state.docente.id_usuario,
            )
        else:
            prefs = cargar_preferencias(
                db_connection, "estudiante_pie", "id_estudiante", st.session_state.estudiante.id_estudiante,
            )
        st.session_state.dua_nocturno = prefs.modo_nocturno
        st.session_state.dua_filtro_pct = prefs.filtro_luz_pct
        st.session_state._dua_ultimo_json = prefs.to_json()

    aplicar_estilos(PreferenciasDUA(
        modo_nocturno=st.session_state.dua_nocturno,
        filtro_luz_pct=st.session_state.dua_filtro_pct,
    ))

    if tipo == "estudiante":
        render_chat_estudiante(st.session_state.estudiante)
    elif tipo == "docente":
        render_panel_docente(st.session_state.docente)
    else:
        st.error("Tipo de usuario no reconocido.")
        cerrar_sesion()
        st.rerun()


main()
