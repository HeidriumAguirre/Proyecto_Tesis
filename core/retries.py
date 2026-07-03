"""
Reintentos y watchdog para la conexion a MySQL.
Tolerancia a microcortes de red cuando el contenedor db_relacional
se reinicia o la red de Docker sufre latencia.
"""
from __future__ import annotations

import logging
from typing import Callable

import pymysql
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# Excepciones transitorias: timeout, conexion rechazada, broken pipe
EXCEPCIONES_TRANSITORIAS = (
    pymysql.err.OperationalError,
    pymysql.err.InterfaceError,
    ConnectionError,
    TimeoutError,
    OSError,
)


def _before_sleep(retry_state) -> None:
    logger.warning(
        "Reintentando operacion MySQL (intento %s) tras error: %s",
        retry_state.attempt_number,
        retry_state.outcome.exception(),
    )


con_reintentos = retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(EXCEPCIONES_TRANSITORIAS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


@con_reintentos
def conectar_con_reintentos(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    connect_timeout: int = 5,
) -> pymysql.connections.Connection:
    """Abre una conexion MySQL aplicando backoff exponencial."""
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=connect_timeout,
        read_timeout=10,
        write_timeout=10,
    )


def asegurar_conexion_viva(conn: pymysql.connections.Connection) -> pymysql.connections.Connection:
    """
    Verifica que la conexion siga viva. Si MySQL cerro el socket por
    wait_timeout, lo reabre con los mismos parametros.
    """
    try:
        conn.ping(reconnect=True)
        return conn
    except EXCEPCIONES_TRANSITORIAS as exc:
        logger.error("Conexion MySQL caida, sera necesario reconectar: %s", exc)
        raise


def ejecutar_query_segura(
    conn: pymysql.connections.Connection,
    sql: str,
    params: tuple | dict | None = None,
    fetch: str = "all",
) -> list[dict] | dict | None:
    """
    Ejecuta una consulta con ping-reconnect automatico.
    fetch: 'all', 'one' o 'none' (para INSERT/UPDATE/DELETE).
    """
    @con_reintentos
    def _ejecutar():
        nonlocal conn
        conn = asegurar_conexion_viva(conn)
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            return None

    return _ejecutar()
