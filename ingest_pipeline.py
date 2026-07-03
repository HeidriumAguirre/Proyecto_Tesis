"""
Pipeline de ingesta de PDFs Mineduc hacia MySQL + ChromaDB.
Uso: python ingest_pipeline.py
"""
import logging
import os
import re
import sys
import uuid

import pymysql
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

import chromadb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import (  # noqa: E402
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)
from core.retries import conectar_con_reintentos  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("its_rag_math.ingest")


db_connection = conectar_con_reintentos(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE,
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
vector_collection = chroma_client.get_or_create_collection(name="mineduc_matematica")


def mapear_metadatos_archivo(nombre_archivo: str) -> dict | None:
    """Parsea el nombre del archivo para extraer tipo, curso y tomo."""
    nombre_upper = nombre_archivo.upper()

    if "TE_" in nombre_upper:
        tipo_doc = "Texto_Escolar"
        label_doc = "Texto del Estudiante"
    elif "GDD_" in nombre_upper:
        tipo_doc = "Guia_Docente"
        label_doc = "Guia Digital del Docente"
    else:
        return None

    if "1B" in nombre_upper:
        curso = "1_Basico"
    elif "2B" in nombre_upper:
        curso = "2_Basico"
    elif "3B" in nombre_upper:
        curso = "3_Basico"
    elif "4B" in nombre_upper:
        curso = "4_Basico"
    else:
        return None

    tomo = "Tomo 1" if "T1" in nombre_upper else "Tomo 2"

    titulo_limpio = f"Matematica {curso.replace('_', ' ')} - {label_doc} ({tomo})"
    return {
        "titulo": titulo_limpio,
        "tipo_documento": tipo_doc,
        "curso": curso,
    }


def ejecutar_ingesta_archivo(path_completo: str, nombre_archivo: str) -> None:
    meta = mapear_metadatos_archivo(nombre_archivo)
    if not meta:
        logger.warning("Archivo omitido por formato no reconocido: %s", nombre_archivo)
        return

    logger.info("Procesando: %s", meta["titulo"])

    loader = PyPDFLoader(path_completo)
    try:
        paginas = loader.load()
    except Exception as e:
        logger.error("Error al leer PDF %s: %s", nombre_archivo, e)
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=140,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = text_splitter.split_documents(paginas)
    logger.info("Fragmentado en %d bloques conceptuales.", len(chunks))

    cursor = db_connection.cursor()
    chunks_exitosos = 0

    for idx, chunk in enumerate(chunks):
        id_recurso_uuid = str(uuid.uuid4())
        prefix = nombre_archivo.lower().split("_catalogo")[0].split("_2026")[0]
        chunk_id_vectorial = f"{prefix}_chunk_{idx}"

        num_pagina = chunk.metadata.get("page", 0) + 1
        texto_contenido = chunk.page_content.strip()
        if not texto_contenido:
            continue

        sql_insert = """
            INSERT INTO recurso_mineduc
            (id_recurso, titulo_documento, tipo_documento, nivel_curso, pagina_referencia, chunk_id_chromadb, url_fuente)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        try:
            cursor.execute(
                sql_insert,
                (
                    id_recurso_uuid,
                    meta["titulo"],
                    meta["tipo_documento"],
                    meta["curso"],
                    num_pagina,
                    chunk_id_vectorial,
                    "https://www.curriculumnacional.cl",
                ),
            )
            vector_collection.add(
                documents=[texto_contenido],
                ids=[chunk_id_vectorial],
                metadatas={
                    "id_recurso_relacional": id_recurso_uuid,
                    "pagina": num_pagina,
                    "curso": meta["curso"],
                    "tipo": meta["tipo_documento"],
                },
            )
            chunks_exitosos += 1
        except pymysql.err.IntegrityError as e:
            if "Duplicate entry" in str(e):
                continue
            logger.error("Error en fragmento %d: %s", idx, e)
        except Exception as e:
            logger.error("Error inesperado en fragmento %d: %s", idx, e)

    db_connection.commit()
    cursor.close()
    logger.info(
        "Sincronizacion exitosa. %d bloques agregados a MySQL y ChromaDB.",
        chunks_exitosos,
    )


def iniciar_ingesta_masiva() -> None:
    directorio_pdfs = "./data/mineduc_pdfs"

    if not os.path.exists(directorio_pdfs):
        logger.error("No existe la ruta %s", directorio_pdfs)
        return

    archivos = [f for f in os.listdir(directorio_pdfs) if f.lower().endswith(".pdf")]

    if not archivos:
        logger.warning("No se encontraron PDFs en %s", directorio_pdfs)
        return

    logger.info("Se detectaron %d documentos listos para el pipeline.", len(archivos))

    for archivo in archivos:
        path_completo = os.path.join(directorio_pdfs, archivo)
        ejecutar_ingesta_archivo(path_completo, archivo)

    logger.info("PROCESO MASIVO FINALIZADO CON EXITO.")


if __name__ == "__main__":
    iniciar_ingesta_masiva()
