"""
Script CLI para probar el flujo ITS sin levantar Streamlit.
Uso: python main.py
"""
import os
import sys
import logging

import pymysql
import chromadb
from google import genai

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import (  # noqa: E402
    GEMINI_API_KEY,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)
from core.prompts import system_instruction_socratico  # noqa: E402
from core.retries import conectar_con_reintentos  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("its_rag_math.cli")


db_connection = conectar_con_reintentos(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE,
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
vector_collection = chroma_client.get_collection(name="mineduc_matematica")

ai_client = genai.Client(api_key=GEMINI_API_KEY)


def obtener_contexto_estudiante_pie(rut_estudiante: str) -> dict | None:
    cursor = db_connection.cursor()
    query = """
        SELECT e.id_estudiante, e.nombre_completo, e.curso,
               e.nivel_adaptacion_lenguaje, e.requiere_apoyo_pictorico,
               (SELECT GROUP_CONCAT(d.codigo SEPARATOR ', ')
                FROM estudiante_diagnostico ed
                JOIN diagnostico d ON ed.id_diagnostico = d.id_diagnostico
                WHERE ed.id_estudiante = e.id_estudiante) AS diagnosticos
        FROM estudiante_pie e
        WHERE e.rut = %s;
    """
    cursor.execute(query, (rut_estudiante,))
    return cursor.fetchone()


def buscar_andamiaje_curricular(consulta: str, curso: str, tipo_documento: str) -> str:
    resultados = vector_collection.query(
        query_texts=[consulta],
        n_results=3,
        where={"$and": [{"curso": curso}, {"tipo": tipo_documento}]},
    )
    docs = resultados.get("documents", [[]])[0]
    return "\n".join(docs) if docs else ""


def simular_interaccion_tutor(rut_alumno: str, pregunta_matematica: str) -> None:
    print("=" * 70)
    print("           SISTEMA DE TUTORIA INTELIGENTE INCLUSIVO (ITS)")
    print("=" * 70)

    alumno = obtener_contexto_estudiante_pie(rut_alumno)
    if not alumno:
        print(f"[-] Error: No se encontro registro PIE para el RUT {rut_alumno}")
        return

    nombre = alumno["nombre_completo"]
    print(
        f"[OK] Alumno: {nombre} | Nivel: {alumno['curso']} | PIE: {alumno['diagnosticos']}"
    )
    print("-" * 70)
    print(f"Estudiante: \"{pregunta_matematica}\"")
    print("-" * 70)

    contexto_pedagogico = buscar_andamiaje_curricular(
        consulta_estudiante=pregunta_matematica,
        curso_filtrar=alumno["curso"],
        tipo_documento="Guia_Docente",
    )

    instructions = system_instruction_socratico(
        nombre=nombre,
        diagnosticos=alumno.get("diagnosticos") or "",
        nivel_adaptacion=alumno.get("nivel_adaptacion_lenguaje") or "",
        requiere_apoyo_pictorico=bool(alumno.get("requiere_apoyo_pictorico")),
        contexto_pedagogico=contexto_pedagogico,
    )

    print("[*] Enviando prompt adaptativo al motor de inferencia GenAI...")

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=pregunta_matematica,
            config=genai.types.GenerateContentConfig(
                system_instruction=instructions,
                temperature=0.3,
            ),
        )
        print("-" * 70)
        print("TUTOR IA SOCRATICO DICE:")
        print("-" * 70)
        print(response.text)
        print("=" * 70)
    except Exception as e:
        print(f"[-] Error en la llamada al modelo de IA: {e}")
        print("[!] Verifica GEMINI_API_KEY en .env")


if __name__ == "__main__":
    if "--test-connection" in sys.argv:
        print("[OK] Conexion exitosa a MySQL.")
        sys.exit(0)
    rut_simulado = "25.123.456-7"
    pregunta_test = "Tengo 12 manzanas y le doy 4 a mi primo, como se cuantas me quedan?"
    simular_interaccion_tutor(rut_simulado, pregunta_test)
