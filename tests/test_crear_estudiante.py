"""
Tests para core.admin.crear_estudiante.
Validan que el id_usuario se inserta correctamente en la columna
id_usuario (no en rut) y que la consulta de recuperacion funciona.
"""
from unittest.mock import MagicMock, patch

import pytest

from core.admin import crear_estudiante


def _mock_conn():
    """Crea un mock basico de conexion."""
    cur = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = False
    return conn, cur


def test_crear_estudiante_orden_parametros_id_usuario():
    """
    REGRESION: el id_usuario generado en Python debe ir a la columna
    id_usuario de estudiante_pie, NO a la columna rut.
    """
    conn, cur = _mock_conn()

    # Mockear obtener_estudiante_por_id para que retorne un Estudiante valido
    # sin tocar la BD (asi no necesitamos fetchone con datos complejos)
    with patch("core.admin.obtener_estudiante_por_id") as mock_get:
        from core.admin import Estudiante
        mock_get.return_value = Estudiante(
            id_estudiante="est-test",
            id_usuario="user-test",
            rut="99.999.999-9",
            nombre_completo="Test Alumno",
            correo_electronico="test@murialdo.cl",
            curso="1_Basico",
            curso_subdivision="A",
            nivel_adaptacion_lenguaje="Alto",
            requiere_apoyo_pictorico=True,
            created_by_usuario="doc-test",
        )

        # Mockear ejecutar_query_segura para el SELECT de recuperacion del id_estudiante
        with patch("core.admin.ejecutar_query_segura") as mock_exec:
            mock_exec.return_value = {"id_estudiante": "est-test"}

            crear_estudiante(
                conn,
                rut="99.999.999-9",
                nombre_completo="Test Alumno",
                correo_electronico="test@murialdo.cl",
                curso="1_Basico",
                curso_subdivision="A",
                nivel_adaptacion_lenguaje="Alto",
                requiere_apoyo_pictorico=True,
                id_docente="doc-uuid-test",
            )

    # El primer execute es el INSERT en usuario.
    # El segundo execute es el INSERT en estudiante_pie.
    assert cur.execute.call_count >= 2, (
        f"Se esperaban al menos 2 execute(), hubo {cur.execute.call_count}"
    )

    sqls = [c[0][0] for c in cur.execute.call_args_list]
    params_list = [c[0][1] for c in cur.execute.call_args_list]

    # Encontrar el INSERT de estudiante_pie
    insert_ep_idx = next(
        (i for i, s in enumerate(sqls) if "INSERT INTO estudiante_pie" in s),
        None,
    )
    assert insert_ep_idx is not None, "No se encontro INSERT INTO estudiante_pie"
    params_ep = params_list[insert_ep_idx]

    # Encontrar el INSERT de usuario (para extraer el id_usuario generado)
    insert_u_idx = next(
        (i for i, s in enumerate(sqls) if "INSERT INTO usuario" in s),
        None,
    )
    id_usuario_generado = params_list[insert_u_idx][0]

    # El primer parametro del INSERT de estudiante_pie DEBE ser el id_usuario
    assert params_ep[0] == id_usuario_generado, (
        f"BUG REGRESION: el primer parametro de estudiante_pie es {params_ep[0]} "
        f"pero deberia ser el id_usuario {id_usuario_generado}"
    )

    # El segundo parametro DEBE ser el RUT real, NO un UUID
    assert params_ep[1] == "99.999.999-9", (
        f"BUG REGRESION: el segundo parametro es {params_ep[1]} pero deberia "
        f"ser el RUT '99.999.999-9'"
    )

    # El SQL NO debe listar id_estudiante explicitamente (usa DEFAULT UUID())
    sql_ep = sqls[insert_ep_idx]
    columnas = sql_ep.split("(")[1].split(")")[0]
    assert "id_estudiante" not in columnas, (
        f"El SQL lista id_estudiante: {columnas}. "
        f"Deberia usar DEFAULT UUID() y no pasarlo en el INSERT."
    )


def test_crear_estudiante_rechaza_curso_invalido():
    conn, _ = _mock_conn()
    with pytest.raises(ValueError, match="Curso invalido"):
        crear_estudiante(
            conn,
            rut="1-1", nombre_completo="x", correo_electronico=None,
            curso="5_Basico", curso_subdivision=None,
            nivel_adaptacion_lenguaje="Alto",
            requiere_apoyo_pictorico=False,
            id_docente="d",
        )


def test_crear_estudiante_rechaza_nivel_invalido():
    conn, _ = _mock_conn()
    with pytest.raises(ValueError, match="Nivel invalido"):
        crear_estudiante(
            conn,
            rut="1-1", nombre_completo="x", correo_electronico=None,
            curso="1_Basico", curso_subdivision=None,
            nivel_adaptacion_lenguaje="SuperAlto",
            requiere_apoyo_pictorico=False,
            id_docente="d",
        )


def test_crear_estudiante_rechaza_subdivision_invalida():
    conn, _ = _mock_conn()
    with pytest.raises(ValueError, match="Subdivision invalida"):
        crear_estudiante(
            conn,
            rut="1-1", nombre_completo="x", correo_electronico=None,
            curso="1_Basico", curso_subdivision="C",
            nivel_adaptacion_lenguaje="Alto",
            requiere_apoyo_pictorico=False,
            id_docente="d",
        )
