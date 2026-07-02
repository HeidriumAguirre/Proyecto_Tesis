import chromadb
import pymysql
from google import genai  # <-- NUEVA LIBRERÍA OFICIAL

from database.connection import test_internal_connection

#================================================================
# Conexion a web localhost: uv run streamlit run app.py
#================================================================

# ================================================================
# CONFIGURACIONES DE CONEXIÓN Y CLIENTES
# ================================================================
db_connection = pymysql.connect(
    host="db_relacional",
    user="root",
    password="demo",
    database="its_murialdo",
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
vector_collection = chroma_client.get_collection(name="mineduc_matematica")

# Inicializamos el cliente de Gemini (Leerá la API KEY desde las variables de entorno)
# Para pruebas locales directas, puedes pasarla como: client = genai.Client(api_key="TU_API_KEY")
ai_client = genai.Client()

# ================================================================
# CAPAS DE DATOS (MYSQL Y CHROMADB)
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
            GROUP BY e.id_estudiante; \
            """
    cursor.execute(query, (rut_estudiante,))
    perfil = cursor.fetchone()
    cursor.close()
    return perfil

def buscar_andamiaje_curricular(consulta_estudiante, curso_filtrar, tipo_documento):
    resultados = vector_collection.query(
        query_texts=[consulta_estudiante],
        n_results=3,
        where={
            "$and": [
                {"curso": curso_filtrar},
                {"tipo": tipo_documento}
            ]
        }
    )
    return resultados

# ================================================================
# ORQUESTADOR CON GENERACIÓN INTERACTIVA (LLM)
# ================================================================
def simular_interaccion_tutor(rut_alumno, pregunta_matematica):
    print("=" * 70)
    print("           SISTEMA DE TUTORÍA INTELIGENTE INCLUSIVO (ITS)")
    print("=" * 70)

    alumno = obtener_contexto_estudiante_pie(rut_alumno)
    if not alumno:
        print(f"[-] Error: No se encontró registro PIE para el RUT {rut_alumno}")
        return

    print(f"[✔] Alumno: {alumno['nombre_completo']} | Nivel: {alumno['curso']} | PIE: {alumno['diagnosticos']}")
    print("-" * 70)
    print(f"👦 Estudiante: \"{pregunta_matematica}\"")
    print("-" * 70)

    # 1. Recuperación RAG (Buscamos en la Guía del Docente de 2° Básico)
    bloques_recuperados = buscar_andamiaje_curricular(
        consulta_estudiante=pregunta_matematica,
        curso_filtrar=alumno['curso'],
        tipo_documento="Guia_Docente"
    )
    contexto_pedagogico = "\n".join(bloques_recuperados['documents'][0])

    # 2. Inyección y Ensamblaje del Prompt Adaptativo
    instructions = f"""
    Eres el Tutor Inteligente de Matemáticas del Colegio San Leonardo Murialdo.
    Atiendes a un alumno con Diagnóstico PIE: {alumno['diagnosticos']}.
    Nivel de Adaptación de Lenguaje: {alumno['nivel_adaptacion_lenguaje']}.
    Requiere Apoyo Pictórico: {alumno['requiere_apoyo_pictorico']}.

    REGLAS DE ORO:
    1. Método SOCRÁTICO estricto: Jamás des el número del resultado. Guíalo con preguntas cortas.
    2. Si el nivel de adaptación es 'Alto', usa frases muy simples, claras y de máximo dos líneas por instrucción. No satures con texto largo.
    3. Si 'Requiere Apoyo Pictórico' es 1, dibuja diagramas sencillos con caracteres planos (ej: [■ ■ ■] o [O O O]) para representar las cantidades concretas que menciona su problema.
    
    Usa este contexto técnico del Mineduc para estructurar tu guía paso a paso:
    {contexto_pedagogico}
    """

    print("[*] Enviando Prompt Adaptativo al motor de inferencia GenAI...")

    try:
        # 3. Llamada al modelo oficial optimizado y rápido (Gemini 2.5 Flash)
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=pregunta_matematica,
            config=genai.types.GenerateContentConfig(
                system_instruction=instructions,
                temperature=0.3 # Baja temperatura para evitar alucinaciones matemáticas
            )
        )

        print("-" * 70)
        print(f"🤖 TUTOR IA SOCRÁTICO DICE:")
        print("-" * 70)
        print(response.text)
        print("=" * 70)

    except Exception as e:
        print(f"[-] Error en la llamada al modelo de IA: {str(e)}")
        print("[!] Asegúrate de configurar tu API Key de Google GenAI.")

if __name__ == "__main__":
    if test_internal_connection():
        rut_simulado = "25.123.456-7"
        pregunta_test = "Tengo 12 manzanas y le doy 4 a mi primo, ¿cómo sé cuántas me quedan? No sé qué hacer."
        simular_interaccion_tutor(rut_simulado, pregunta_test)