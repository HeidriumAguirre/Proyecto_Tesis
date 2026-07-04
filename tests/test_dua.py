"""
Tests para core.dua (preferencias y serializacion JSON).
No requieren conexion a MySQL.
"""
from core.dua import PreferenciasDUA


def test_preferencias_defaults():
    p = PreferenciasDUA()
    assert p.modo_nocturno is False
    assert p.filtro_luz_pct == 0


def test_preferencias_to_json_roundtrip():
    p = PreferenciasDUA(modo_nocturno=True, filtro_luz_pct=75)
    raw = p.to_json()
    p2 = PreferenciasDUA.from_json(raw)
    assert p2.modo_nocturno is True
    assert p2.filtro_luz_pct == 75


def test_from_json_none_devuelve_defaults():
    p = PreferenciasDUA.from_json(None)
    assert p.modo_nocturno is False
    assert p.filtro_luz_pct == 0


def test_from_json_invalido_devuelve_defaults():
    p = PreferenciasDUA.from_json("esto no es json")
    assert p.modo_nocturno is False
    assert p.filtro_luz_pct == 0


def test_from_json_dict_parcial():
    p = PreferenciasDUA.from_json('{"modo_nocturno": true}')
    assert p.modo_nocturno is True
    assert p.filtro_luz_pct == 0


def test_from_json_acepta_dict_directo():
    """PyMySQL puede devolver JSON como dict en lugar de string."""
    p = PreferenciasDUA.from_json({"modo_nocturno": True, "filtro_luz_pct": 50})
    assert p.modo_nocturno is True
    assert p.filtro_luz_pct == 50


def test_from_json_legacy_con_filtro_luz_bool():
    """Compatibilidad con el formato antiguo (bool en vez de pct)."""
    p = PreferenciasDUA.from_json('{"modo_nocturno": false, "filtro_luz": true}')
    assert p.modo_nocturno is False
    assert p.filtro_luz_pct == 50  # mapeo legacy


def test_from_json_clamp_filtro_pct():
    """Si el valor esta fuera de rango, se clampea a [0, 100]."""
    p = PreferenciasDUA.from_json('{"filtro_luz_pct": 150}')
    assert p.filtro_luz_pct == 100
    p = PreferenciasDUA.from_json('{"filtro_luz_pct": -20}')
    assert p.filtro_luz_pct == 0
