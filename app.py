import streamlit as str_visual
import streamlit.components.v1 as html_visual  # <-- IMPORTACIÓN CLAVE PARA EL AUDIO AISLADO
import pymysql
import chromadb
from google import genai
import os
from PIL import Image

# ================================================================
# A. CONFIGURACIONES DE SEGURIDAD (API Key Inyectada)
# ================================================================
os.environ["GEMINI_API_KEY"] = "AIzaSyDSaoXY1w8cWFeVcfvcMjFX4NfygJSl9pk"

# ================================================================
# B. INICIALIZACIÓN OPTIMIZADA CON CACHÉ INDEPENDIENTE
# ================================================================

@str_visual.cache_resource
def obtener_conexion_mysql():
    """Mantiene la conexión relacional activa sin duplicarla en cada clic."""
    return pymysql.connect(
        host="db_relacional",
        user="root",
        password="demo",
        database="its_murialdo",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

@str_visual.cache_resource
def obtener_cliente_chroma():
    """Mantiene mapeados los índices vectoriales densos en memoria RAM."""
    chroma = chromadb.PersistentClient(path="./chroma_db")
    # CAMBIA ESTO: Usa get_or_create_collection para que no explote si no existe
    return chroma.get_or_create_collection(name="mineduc_matematica")

@str_visual.cache_resource
def obtener_cliente_gemini():
    """Conserva la instancia del SDK generativo activa."""
    return genai.Client()

# Carga segura usando los recursos cacheados de Streamlit
try:
    db_connection = obtener_conexion_mysql()
    vector_collection = obtener_cliente_chroma()
    ai_client = obtener_cliente_gemini()
except Exception as e:
    str_visual.error(f"Error crítico en capa de inicialización: {str(e)}")
    str_visual.stop()

# ================================================================
# 1. IDENTIDAD VISUAL CORPORATIVA (BLANCO, AZUL Y SÓCRATES)
# ================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_insignia_ok = os.path.join(BASE_DIR, "data", "assets", "insignia_principal.png")
ruta_icono_ok = os.path.join(BASE_DIR, "data", "assets", "icono_murialdo.png.png")
if not os.path.exists(ruta_icono_ok):
    ruta_icono_ok = os.path.join(BASE_DIR, "data", "assets", "icono_murialdo.png")

ruta_avatar_socrates = os.path.join(BASE_DIR, "data", "assets", "socrates.png")

try:
    path_insignia = Image.open(ruta_insignia_ok)
    path_icono = Image.open(ruta_icono_ok)
except Exception as e:
    str_visual.error(f"⚠️ Error cargando insignias locales: {str(e)}")
    str_visual.stop()

str_visual.set_page_config(
    page_title="ITS - Colegio Murialdo Valparaíso",
    page_icon=path_icono,
    layout="centered"
)

str_visual.markdown("""
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
    </style>
""", unsafe_allow_html=True)

# ================================================================
# 2. CAPA DE DATA (LOGICA SQL + RAG)
# ================================================================
def obtener_contexto_estudiante_pie(rut_estudiante):
    cursor = db_connection.cursor()
    query = """
            SELECT e.id_estudiante, e.nombre_completo, e.curso,
                   e.nivel_adaptacion_lenguaje, e.requiere_apoyo_pictorico,
                   GROUP_CONCAT(d.codigo SEPARATOR ', ') as diagnosticos
            FROM estudiante_pie e
                     LEFT JOIN estudiante_diagnostico ed ON e.id_estudiante = ed.id_estudiante
                     LEFT JOIN diagnostico d ON ed.id_diagnostico = d.id_diagnostico
            WHERE e.rut = %s
            GROUP BY e.id_estudiante;
            """
    cursor.execute(query, (rut_estudiante,))
    perfil = cursor.fetchone()
    cursor.close()
    return perfil

def buscar_andamiaje_curricular(consulta, curso, tipo_doc):
    resultados = vector_collection.query(
        query_texts=[consulta],
        n_results=3,
        where={"$and": [{"curso": curso}, {"tipo": tipo_doc}]}
    )
    return "\n".join(resultados['documents'][0])

def cargar_mensajes_anteriores(id_sesion):
    try:
        cursor = db_connection.cursor()
        query = """
                SELECT remitente, contenido_mensaje
                FROM historial_interaccion
                WHERE id_sesion = %s
                ORDER BY fecha_envio ASC;
                """
        cursor.execute(query, (id_sesion,))
        registros = cursor.fetchall()
        cursor.close()

        mensajes_formateados = []
        for reg in registros:
            role = "user" if reg['remitente'] == 'Estudiante' else "assistant"
            mensajes_formateados.append({"role": role, "content": reg['contenido_mensaje']})
        return mensajes_formateados
    except Exception as e:
        print(f"Error cargando historial desde MySQL: {str(e)}")
        return []

def guardar_mensaje_en_historial(id_sesion, remitente, contenido_mensaje, id_recurso=None):
    try:
        cursor = db_connection.cursor()
        query = """
                INSERT INTO historial_interaccion (id_sesion, id_recurso, remitente, contenido_mensaje)
                VALUES (%s, %s, %s, %s);
                """
        cursor.execute(query, (id_sesion, id_recurso, remitente, contenido_mensaje))
        db_connection.commit()
        cursor.close()
    except Exception as e:
        print(f"Error al persistir interacción en MySQL: {str(e)}")

# ================================================================
# 3. DISEÑO DE LA INTERFAZ WEB
# ================================================================

col_logo, col_titulo = str_visual.columns([1, 4])
with col_logo:
    str_visual.image(path_insignia, width=110)
with col_titulo:
    str_visual.markdown("<div class='header-title-murialdo'>COLEGIO MURIALDO VALPARAÍSO</div>", unsafe_allow_html=True)
    str_visual.markdown("<div class='header-subtitle-murialdo'>Plataforma RAG de Acompañamiento Matemático Inclusivo</div>", unsafe_allow_html=True)

str_visual.markdown("---")

# ================================================================
# CONTROL DE SESIÓN PILOTO
# ================================================================
if "id_sesion" not in str_visual.session_state:
    id_piloto_fijo = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

    try:
        cursor = db_connection.cursor()
        cursor.execute("SELECT id_sesion FROM sesion_tutoria WHERE id_sesion = %s", (id_piloto_fijo,))
        existe_sesion = cursor.fetchone()

        if not existe_sesion:
            cursor.execute("SELECT id_estudiante FROM estudiante_pie LIMIT 1")
            res_estudiante = cursor.fetchone()

            cursor.execute("SELECT id_oa FROM objetivo_aprendizaje LIMIT 1")
            res_oa = cursor.fetchone()

            if res_estudiante and res_oa:
                id_estudiante_valido = res_estudiante['id_estudiante']
                id_oa_valido = res_oa['id_oa']

                query_padre = """
                              INSERT INTO sesion_tutoria (
                                  id_sesion, id_estudiante, id_oa, fecha_inicio, fecha_fin, estado_emocional_inicial, estado_sesion
                              )
                              VALUES (%s, %s, %s, NOW(), NULL, 'Neutro', 'Activa');
                              """
                cursor.execute(query_padre, (id_piloto_fijo, id_estudiante_valido, id_oa_valido))
                db_connection.commit()
                print("¡Estupendo! Sesión piloto vinculada correctamente en MySQL.")
            else:
                print("⚠️ ATENCIÓN: Asegúrate de haber guardado al menos una fila en 'objetivo_aprendizaje' and 'estudiante_pie'.")

        cursor.close()
    except Exception as e:
        print(f"Error crítico al preparar sesión automática en MySQL: {str(e)}")

    str_visual.session_state.id_sesion = id_piloto_fijo

# ================================================================
# CARGA DEL HISTORIAL DESDE LA BASE DE DATOS
# ================================================================
if "messages" not in str_visual.session_state:
    historial_bd = cargar_mensajes_anteriores(str_visual.session_state.id_sesion)
    str_visual.session_state.messages = historial_bd

rut_piloto = "25.123.456-7"
alumno = obtener_contexto_estudiante_pie(rut_piloto)

if alumno:
    partes_nombre = alumno['nombre_completo'].split()
    nombre_corto = f"{partes_nombre[0]} {partes_nombre[2]}" if len(partes_nombre) >= 3 else alumno['nombre_completo']

    str_visual.markdown(f"""
        <div class='perfil-card-estudiante'>
            <div style='color: #0F2C59; font-size: 18px; font-weight: 700; margin-bottom: 8px;'>🟠 Mi Panel de Matemáticas</div>
            <div style='font-size: 15px; color: #444444; line-height: 1.6;'>
                <b>Estudiante:</b> {nombre_corto}<br>
                <b>Curso:</b> {alumno['curso'].replace('_', ' ')} Básicos<br>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ================================================================
# RENDERIZADO DEL HISTORIAL CON LIMPIEZA DINÁMICA EN EL NAVEGADOR
# ================================================================
for i, msg in enumerate(str_visual.session_state.messages):
    avatar_chat = ruta_avatar_socrates if msg["role"] == "assistant" else "👦"
    with str_visual.chat_message(msg["role"], avatar=avatar_chat):
        str_visual.markdown(msg["content"])

        if msg["role"] == "assistant":
            # 1. Limpieza ultra básica en Python para no romper las comillas o saltos de JavaScript
            texto_seguro = msg["content"].replace("\n", " ").replace("'", "").replace('"', '').replace('`', '')

            # 2. Reutilizamos html_visual.html pasándole las reglas de limpieza directamente a JS
            html_visual.html(f"""
                <script>
                function hablar() {{
                    window.speechSynthesis.cancel();
                    
                    // Capturamos el texto inyectado
                    let textoOriginal = '{texto_seguro}';
                    
                    // LIMPIEZA DE CARACTERES EN EL FRONTEND:
                    let textoLimpio = textoOriginal.replace(/[\\*#\\-_`]/g, "");
                    
                    // B. Filtramos emojis comunes de frutas y figuras para que no los deletree
                    textoLimpio = textoLimpio.replace(/[🍏🍎🍊🍋🍌🍉🍇🍓🍒🍑🥭🍍🍅🍆🥔🥕🌽🌶️🫑🧅🧄🥑🥦🥬🥒🫛🌶️🔸🔹🔶🔷🔺🔻👉👈👉]/gu, "");
                    
                    // C. Limpiamos espacios dobles residuales
                    textoLimpio = textoLimpio.replace(/\\s+/g, " ").trim();

                    // Respaldo por si se vacía por completo el string
                    if (!textoLimpio) textoLimpio = textoOriginal;

                    let u = new SpeechSynthesisUtterance(textoLimpio);
                    u.lang = 'es-CL';
                    u.rate = 0.95;
                    window.speechSynthesis.speak(u);
                }}
                </script>
                <button onclick="hablar()" style="
                    background-color: #0F2C59; color: white; border: none; 
                    padding: 8px 16px; border-radius: 20px; cursor: pointer; 
                    font-size: 13px; font-weight: bold; font-family: sans-serif;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
                ">
                    🔊 Escuchar a Sócrates
                </button>
            """, height=45)

# ================================================================
# 4. ENTRADAS DE MATEO (Teclado Tradicional)
# ================================================================
pregunta_usuario = str_visual.chat_input("Escribe aquí tu duda de matemáticas, Mateo...")

# ================================================================
# 5. PROCESAMIENTO DE LA INTERACCIÓN
# ================================================================
if pregunta_usuario:
    with str_visual.chat_message("user", avatar="👦"):
        str_visual.markdown(pregunta_usuario)

    str_visual.session_state.messages.append({"role": "user", "content": pregunta_usuario})

    guardar_mensaje_en_historial(
        id_sesion=str_visual.session_state.id_sesion,
        remitente='Estudiante',
        contenido_mensaje=pregunta_usuario
    )

    with str_visual.spinner("✨ Consultando el libro oficial del Mineduc..."):
        contexto_mineduc = buscar_andamiaje_curricular(pregunta_usuario, alumno['curso'], "Guia_Docente")

        system_instructions = f"""
        Eres el Tutor Inteligente de Matemáticas del Colegio San Leonardo Murialdo.
        Atiendes a un alumno con Diagnóstico PIE: TEA.
        Nivel de Adaptación de Lenguaje: Alto (Poco texto, oraciones corta).
        Requiere Apoyo Pictórico: Sí (Usa manzanas, diagramas o emojis).

        REGLAS DE ORO SOCRÁTICAS:
        1. Jamás des el número del resultado. Guíalo con preguntas muy cortas.
        2. Valida su frustración. Felicita cada pequeño logro.
        3. Si se equivoca en un cálculo, no digas 'mal'. Redibuja la cantidad visual y dile: '¡Casi! Vamos a contar juntos de nuevo con cuidado'.
        
        Usa el contexto pedagógico oficial del Mineduc recuperado de ChromaDB:
        {contexto_mineduc}
        """

        try:
            conversacion_acumulada = ""
            for m in str_visual.session_state.messages:
                if m["role"] == "user":
                    conversacion_acumulada += f"\nAlumno Mateo: {m['content']}"
                else:
                    conversacion_acumulada += f"\nTutor Socrático: {m['content']}"

            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=conversacion_acumulada,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_instructions,
                    temperature=0.3
                )
            )

            respuesta_tutor = response.text
            str_visual.session_state.messages.append({"role": "assistant", "content": respuesta_tutor})

            guardar_mensaje_en_historial(
                id_sesion=str_visual.session_state.id_sesion,
                remitente='Tutor_IA',
                contenido_mensaje=respuesta_tutor,
                id_recurso=None
            )

            str_visual.rerun()

        except Exception as e:
            str_visual.error(f"Error GenAI: {str(e)}")