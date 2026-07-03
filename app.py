"""
ITS RAG Math - Colegio Murialdo Valparaiso
Sistema de Tutoria Inteligente inclusivo para estudiantes PIE.

Punto de entrada Streamlit. Arquitectura:
- MySQL relacional (perfil PIE, historial de sesion).
- ChromaDB vectorial (andamiaje curricular Mineduc).
- Gemini 2.5 Flash multimodal (texto + audio).
- Entrada por teclado Y por voz (streamlit-mic-recorder).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from typing import Any

import pymysql
import streamlit as st
import streamlit.components.v1 as html_visual
from google import genai
from PIL import Image
from streamlit_mic_recorder import mic_recorder

# --- Path para imports cuando se corre como script -------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import (  # noqa: E402
    GEMINI_API_KEY,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
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
# A. RECURSOS CACHEADOS (conexiones y clientes)
# ============================================================================

@st.cache_resource(show_spinner="Conectando a MySQL...")
def obtener_conexion_mysql() -> pymysql.connections.Connection:
    """Apertura resiliente de la conexion relacional con reintentos."""
    logger.info("Abriendo conexion MySQL hacia %s:%s/%s", MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE)
    return conectar_con_reintentos(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )


@st.cache_resource(show_spinner="Cargando indice vectorial...")
def obtener_cliente_chroma():
    """Mantiene mapeados los indices vectoriales densos en memoria RAM."""
    chroma = __import__("chromadb").PersistentClient(path="./chroma_db")
    return chroma.get_or_create_collection(name="mineduc_matematica")


@st.cache_resource(show_spinner="Inicializando cliente Gemini...")
def obtener_cliente_gemini():
    """Conserva la instancia del SDK generativo activa."""
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
# B. CAPA DE DATOS (MySQL + RAG)
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def obtener_contexto_estudiante_pie(rut_estudiante: str) -> dict | None:
    """Lee el perfil PIE del estudiante. Cacheado 5 min para evitar golpear MySQL."""
    sql = """
        SELECT e.id_estudiante, e.nombre_completo, e.curso, e.rut,
               e.nivel_adaptacion_lenguaje, e.requiere_apoyo_pictorico,
               GROUP_CONCAT(d.codigo SEPARATOR ', ') AS diagnosticos
        FROM estudiante_pie e
        LEFT JOIN estudiante_diagnostico ed ON e.id_estudiante = ed.id_estudiante
        LEFT JOIN diagnostico d ON ed.id_diagnostico = d.id_diagnostico
        WHERE e.rut = %s
        GROUP BY e.id_estudiante;
    """
    try:
        return ejecutar_query_segura(db_connection, sql, (rut_estudiante,), fetch="one")
    except Exception:
        logger.exception("Error leyendo perfil PIE para RUT %s", rut_estudiante)
        return None


def buscar_andamiaje_curricular(consulta: str, curso: str, tipo_doc: str) -> str:
    """Recupera hasta 3 chunks de ChromaDB filtrados por curso y tipo."""
    try:
        resultados = vector_collection.query(
            query_texts=[consulta],
            n_results=3,
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
        ORDER BY fecha_envio ASC;
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
    id_sesion: str,
    remitente: str,
    contenido_mensaje: str,
    id_recurso: str | None = None,
) -> None:
    sql = """
        INSERT INTO historial_interaccion (id_sesion, id_recurso, remitente, contenido_mensaje)
        VALUES (%s, %s, %s, %s);
    """
    try:
        ejecutar_query_segura(
            db_connection,
            sql,
            (id_sesion, id_recurso, remitente, contenido_mensaje),
            fetch="none",
        )
    except Exception:
        logger.exception("Error al persistir interaccion en MySQL")


def preparar_sesion_piloto(id_sesion: str, id_estudiante: int, id_oa: int) -> None:
    sql = """
        INSERT INTO sesion_tutoria
            (id_sesion, id_estudiante, id_oa, fecha_inicio, fecha_fin, estado_emocional_inicial, estado_sesion)
        VALUES (%s, %s, %s, NOW(), NULL, 'Neutro', 'Activa');
    """
    try:
        ejecutar_query_segura(
            db_connection, sql, (id_sesion, id_estudiante, id_oa), fetch="none"
        )
        logger.info("Sesion %s vinculada correctamente", id_sesion)
    except Exception:
        logger.exception("Error creando sesion %s", id_sesion)


def asegurar_sesion_activa(id_sesion: str) -> None:
    """Crea la sesion si no existe, eligiendo primer estudiante y OA disponibles."""
    try:
        existe = ejecutar_query_segura(
            db_connection,
            "SELECT id_sesion FROM sesion_tutoria WHERE id_sesion = %s",
            (id_sesion,),
            fetch="one",
        )
        if existe:
            return

        res_estudiante = ejecutar_query_segura(
            db_connection,
            "SELECT id_estudiante FROM estudiante_pie LIMIT 1",
            fetch="one",
        )
        res_oa = ejecutar_query_segura(
            db_connection,
            "SELECT id_oa FROM objetivo_aprendizaje LIMIT 1",
            fetch="one",
        )

        if res_estudiante and res_oa:
            preparar_sesion_piloto(id_sesion, res_estudiante["id_estudiante"], res_oa["id_oa"])
        else:
            st.warning(
                "Asegurate de haber guardado al menos una fila en "
                "'objetivo_aprendizaje' y 'estudiante_pie'."
            )
    except Exception:
        logger.exception("Error asegurando sesion activa")


# ============================================================================
# C. PROMPT Y LLAMADA AL LLM
# ============================================================================


def llamar_gemini_texto(system_instruction: str, conversacion: str) -> str:
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=conversacion,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
        ),
    )
    return response.text


def llamar_gemini_audio(
    system_instruction: str,
    audio_bytes: bytes,
    mime_type: str = "audio/wav",
) -> str:
    """Envia el audio directamente al modelo multimodal de Gemini."""
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
            system_instruction=system_instruction,
            temperature=0.3,
        ),
    )
    return response.text


# ============================================================================
# D. IDENTIDAD VISUAL Y ASSETS
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
    page_icon=icono_img,
    layout="centered",
)

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
        color: #0F2C59 !important;
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -1px;
        text-align: center;
        margin-top: -15px;
        text-transform: uppercase;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    .header-subtitle-murialdo {
        color: #555555 !important;
        font-size: 16px;
        font-weight: 400;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    .perfil-card-estudiante {
        background-color: #FFFFFF !important;
        border-top: 4px solid #FFD700 !important;
        border-left: 1px solid #E1E8ED !important;
        border-right: 1px solid #E1E8ED !important;
        border-bottom: 1px solid #E1E8ED !important;
        padding: 18px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 25px;
    }
    div[data-testid="stChatMessage"] {
        background-color: #F8F9FA;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px solid #EEEEEE;
    }
    div[data-testid="stChatMessageAssistant"] {
        background-color: #FFFFFF !important;
        border-left: 6px solid #0F2C59;
    }
    .transcripcion-box {
        background-color: #E8F0FE;
        border-left: 3px solid #1A73E8;
        padding: 8px 12px;
        margin: 4px 0 8px 0;
        border-radius: 4px;
        font-size: 13px;
        color: #174EA6 !important;
        font-style: italic;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# E. CABECERA Y SELECCION DE ESTUDIANTE
# ============================================================================

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

# Login del estudiante por RUT. Por defecto vacio (sin piloto cosido al codigo).
rut_input = st.text_input(
    "RUT del estudiante",
    value=st.session_state.get("rut_estudiante", ""),
    placeholder="12.345.678-9",
    help="Ingresa el RUT del estudiante PIE para cargar su perfil.",
    key="rut_input_widget",
)

if rut_input and rut_input != st.session_state.get("rut_estudiante"):
    st.session_state.rut_estudiante = rut_input
    # Invalidar caches que dependan del estudiante
    st.cache_data.clear()
    st.rerun()

rut_piloto = st.session_state.get("rut_estudiante", "").strip()
alumno = obtener_contexto_estudiante_pie(rut_piloto) if rut_piloto else None

if not alumno:
    st.info("Ingresa un RUT valido para comenzar. (Perfil PIE no encontrado)")
    st.stop()

partes_nombre = alumno["nombre_completo"].split()
nombre_corto = (
    f"{partes_nombre[0]} {partes_nombre[2]}"
    if len(partes_nombre) >= 3
    else alumno["nombre_completo"]
)

st.markdown(
    f"""
    <div class='perfil-card-estudiante'>
        <div style='color: #0F2C59; font-size: 18px; font-weight: 700; margin-bottom: 8px;'>
            Mi Panel de Matematicas
        </div>
        <div style='font-size: 15px; color: #444444; line-height: 1.6;'>
            <b>Estudiante:</b> {nombre_corto}<br>
            <b>Curso:</b> {alumno['curso'].replace('_', ' ')} Basicos<br>
            <b>Diagnostico:</b> {alumno.get('diagnosticos') or 'Sin diagnostico registrado'}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# id_sesion dinamico por estudiante, persistido en session_state
if "id_sesion" not in st.session_state:
    st.session_state.id_sesion = str(uuid.uuid4())
    asegurar_sesion_activa(st.session_state.id_sesion)

# Carga inicial del historial
if "messages" not in st.session_state:
    st.session_state.messages = cargar_mensajes_anteriores(st.session_state.id_sesion)


# ============================================================================
# F. RENDERIZADO DEL HISTORIAL CON TTS SEGURO (json.dumps)
# ============================================================================

def render_boton_escuchar(texto: str, key: str) -> None:
    """Inyecta JS con json.dumps para escapar correctamente el texto."""
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
                .replace(/\\s+/g, " ")
                .trim() || textoOriginal;
            const u = new SpeechSynthesisUtterance(textoLimpio);
            u.lang = 'es-CL';
            u.rate = 0.95;
            window.speechSynthesis.speak(u);
        }}
        </script>
        <button onclick="hablar_{key}()" style="
            background-color: #0F2C59; color: white; border: none;
            padding: 8px 16px; border-radius: 20px; cursor: pointer;
            font-size: 13px; font-weight: bold; font-family: sans-serif;
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        ">
            Escuchar a Socrates
        </button>
        """,
        height=45,
    )


for i, msg in enumerate(st.session_state.messages):
    avatar = ruta_avatar_socrates if msg["role"] == "assistant" else "🙋"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_boton_escuchar(msg["content"], key=f"tts_{i}")


# ============================================================================
# G. ENTRADAS (TECLADO + MICROFONO)
# ============================================================================

pregunta_texto = st.chat_input(f"Escribe tu duda, {nombre_corto.split()[0]}...")

st.markdown("##### O habla con Socrates (micrófono)")
audio_grabado = mic_recorder(
    start_prompt="🎤 Grabar",
    stop_prompt="⏹️ Detener",
    just_once=False,
    use_container_width=True,
    key="mic_recorder_principal",
)

pregunta_usuario: str | None = pregunta_texto
transcripcion_audio: str | None = None
es_input_voz = False

if audio_grabado and audio_grabado.get("bytes"):
    es_input_voz = True
    with st.spinner("🎙️ Transcribiendo audio y preparando respuesta..."):
        try:
            contexto_mineduc = buscar_andamiaje_curricular(
                consulta="consulta hablada del estudiante",
                curso=alumno["curso"],
                tipo_doc="Guia_Docente",
            )
            system_inst = system_instruction_socratico(
                nombre=nombre_corto,
                diagnosticos=alumno.get("diagnosticos") or "",
                nivel_adaptacion=alumno.get("nivel_adaptacion_lenguaje") or "",
                requiere_apoyo_pictorico=bool(alumno.get("requiere_apoyo_pictorico")),
                contexto_pedagogico=contexto_mineduc,
            )
            resultado_llm = llamar_gemini_audio(
                system_inst,
                audio_grabado["bytes"],
                mime_type="audio/wav",
            )
            transcripcion_audio, pregunta_usuario = separar_transcripcion_y_respuesta(
                resultado_llm
            )
            if not pregunta_usuario:
                pregunta_usuario = transcripcion_audio or "(no se pudo transcribir)"
        except Exception as e:
            st.error(f"Error al procesar audio: {e}")
            logger.exception("Error en pipeline de audio")
            pregunta_usuario = None


# ============================================================================
# H. PROCESAMIENTO DE LA INTERACCION
# ============================================================================

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
        id_sesion=st.session_state.id_sesion,
        remitente="Estudiante",
        contenido_mensaje=pregunta_usuario,
    )

    with st.spinner("✨ Consultando el libro oficial del Mineduc..."):
        try:
            contexto_mineduc = buscar_andamiaje_curricular(
                pregunta_usuario, alumno["curso"], "Guia_Docente"
            )
            system_inst = system_instruction_socratico(
                nombre=nombre_corto,
                diagnosticos=alumno.get("diagnosticos") or "",
                nivel_adaptacion=alumno.get("nivel_adaptacion_lenguaje") or "",
                requiere_apoyo_pictorico=bool(alumno.get("requiere_apoyo_pictorico")),
                contexto_pedagogico=contexto_mineduc,
            )
            conversacion = construir_contexto_ventana(st.session_state.messages)
            respuesta_tutor = llamar_gemini_texto(system_inst, conversacion)

            st.session_state.messages.append(
                {"role": "assistant", "content": respuesta_tutor}
            )
            guardar_mensaje_en_historial(
                id_sesion=st.session_state.id_sesion,
                remitente="Tutor_IA",
                contenido_mensaje=respuesta_tutor,
            )
        except Exception as e:
            st.error(f"Error GenAI: {e}")
            logger.exception("Error en llamada a Gemini")
            st.stop()

    st.rerun()
