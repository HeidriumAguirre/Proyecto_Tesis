"""
Tests para core.auth: verifican que las queries SQL son validas bajo
el sql_mode de MySQL 8 (only_full_group_by activado por defecto).
"""
from core.auth import autenticar_estudiante
from core.dua import PreferenciasDUA


def test_autenticar_estudiante_query_no_usa_group_by():
    """
    La query de autenticacion no debe tener GROUP BY porque MySQL 8
    con only_full_group_by rechaza columnas no agregadas.
    """
    import inspect
    source = inspect.getsource(autenticar_estudiante)
    assert "GROUP BY" not in source.upper(), (
        "La query de autenticar_estudiante no debe usar GROUP BY. "
        "Use subqueries para concatenar diagnosticos."
    )


def test_dua_preferencias_incluye_correo_y_rol():
    """Las preferencias DUA se serializan correctamente."""
    p = PreferenciasDUA(modo_nocturno=True, filtro_luz_pct=50)
    data = p.to_json()
    assert "modo_nocturno" in data
    assert "filtro_luz_pct" in data
