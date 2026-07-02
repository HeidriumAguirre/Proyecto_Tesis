import os
import re
import uuid
import pymysql
import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ================================================================
# 1. CONFIGURACIONES DE CONEXIÓN (CONTRASENA: demo)
# ================================================================
db_connection = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="demo",
    database="its_murialdo",
    autocommit=True
)

# Inicializar ChromaDB persistente local en tu directorio
chroma_client = chromadb.PersistentClient(path="./chroma_db")
vector_collection = chroma_client.get_or_create_collection(name="mineduc_matematica")

# ================================================================
# 2. MOTOR DE PARSEO AUTOMÁTICO DE ARCHIVOS
# ================================================================
def mapear_metadatos_archivo(nombre_archivo):
    """
    Analiza el nombre del archivo usando expresiones regulares para extraer
    automaticamente el Tipo de Documento, Curso y Tomo.
    """
    nombre_upper = nombre_archivo.upper()

    # Determinar Tipo de Documento
    if "TE_" in nombre_upper:
        tipo_doc = "Texto_Escolar"
        label_doc = "Texto del Estudiante"
    elif "GDD_" in nombre_upper:
        tipo_doc = "Guia_Docente"
        label_doc = "Guia Digital del Docente"
    else:
        return None

    # Determinar Curso
    if "1B" in nombre_upper: curso = "1_Basico"
    elif "2B" in nombre_upper: curso = "2_Basico"
    elif "3B" in nombre_upper: curso = "3_Basico"
    elif "4B" in nombre_upper: curso = "4_Basico"
    else: return None

    # Determinar Tomo
    tomo = "Tomo 1" if "T1" in nombre_upper else "Tomo 2"

    titulo_limpio = f"Matematica {curso.replace('_', ' ')} - {label_doc} ({tomo})"

    return {
        "titulo": titulo_limpio,
        "tipo_documento": tipo_doc,
        "curso": curso
    }

# ================================================================
# 3. PIPELINE DE INGESTA INTEGRADA (RELACIONAL + VECTORIAL)
# ================================================================
def ejecutar_ingesta_archivo(path_completo, nombre_archivo):
    meta = mapear_metadatos_archivo(nombre_archivo)
    if not meta:
        print(f"[-] Archivo omitido por formato no reconocido: {nombre_archivo}")
        return

    print(f"\n[*] Procesando: {meta['titulo']}")

    # Carga del PDF
    loader = PyPDFLoader(path_completo)
    try:
        paginas = loader.load()
    except Exception as e:
        print(f"[-] Error al leer el PDF {nombre_archivo}: {str(e)}")
        return

    # Chunking Semantico/Procedimental orientado a matematicas elementales
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=140,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(paginas)
    print(f"[+] Fragmentado en {len(chunks)} bloques conceptuales.")

    cursor = db_connection.cursor()
    chunks_exitosos = 0

    for idx, chunk in enumerate(chunks):
        id_recurso_uuid = str(uuid.uuid4())
        # Formato de ID unico para ChromaDB: gdd_1b_t1_chunk_42
        prefix = nombre_archivo.lower().split("_catalogo")[0].split("_2026")[0]
        chunk_id_vectorial = f"{prefix}_chunk_{idx}"

        num_pagina = chunk.metadata.get("page", 0) + 1
        texto_contenido = chunk.page_content.strip()

        if not texto_contenido:
            continue

        # SQL para tabla 'recurso_mineduc' creada en tu script
        sql_insert = """
                     INSERT INTO recurso_mineduc
                     (id_recurso, titulo_documento, tipo_documento, nivel_curso, pagina_referencia, chunk_id_chromadb, url_fuente)
                     VALUES (%s, %s, %s, %s, %s, %s, %s); \
                     """

        try:
            # 1. Persistencia Relacional (MySQL)
            cursor.execute(sql_insert, (
                id_recurso_uuid,
                meta["titulo"],
                meta["tipo_documento"],
                meta["curso"],
                num_pagina,
                chunk_id_vectorial,
                "https://www.curriculumnacional.cl"
            ))

            # 2. Persistencia Vectorial (ChromaDB)
            vector_collection.add(
                documents=[texto_contenido],
                ids=[chunk_id_vectorial],
                metadatas={
                    "id_recurso_relacional": id_recurso_uuid,
                    "pagina": num_pagina,
                    "curso": meta["curso"],
                    "tipo": meta["tipo_documento"]
                }
            )
            chunks_exitosos += 1

        except Exception as e:
            # Captura y omite duplicados si se corre el script dos veces
            if "Duplicate entry" in str(e):
                continue
            print(f"[-] Error en fragmento {idx}: {str(e)}")

    cursor.close()
    print(f"[✔] Sincronizacion exitosa. {chunks_exitosos} bloques agregados a MySQL y ChromaDB.")

# ================================================================
# 4. ORQUESTADOR AUTOMÁTICO DE LOTES (BATCH BROWSER)
# ================================================================
def iniciar_ingesta_masiva():
    directorio_pdfs = "./data/mineduc_pdfs"

    if not os.path.exists(directorio_pdfs):
        print(f"[-] Error: No existe la ruta {directorio_pdfs}")
        return

    archivos = [f for f in os.listdir(directorio_pdfs) if f.lower().endswith(".pdf")]

    if not archivos:
        print(f"[-] No se encontraron archivos PDF en {directorio_pdfs}")
        print("[!] Por favor arrastra los archivos descargados a esa carpeta en IntelliJ.")
        return

    print(f"[==] Se detectaron {len(archivos)} documentos listos para el pipeline. [==]")

    for archivo in archivos:
        path_completo = os.path.join(directorio_pdfs, archivo)
        ejecutar_ingesta_archivo(path_completo, archivo)

    print("\n[✔✔✔] PROCESO MASIVO FINALIZADO CON ÉXITO [✔✔✔]")

if __name__ == "__main__":
    iniciar_ingesta_masiva()