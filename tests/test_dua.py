"""
Tests para core.dua (preferencias y serializacion JSON).
No requieren conexion a MySQL.
"""
from core.dua import PreferenciasDUA


def test_preferencias_defaults():
    p = PreferenciasDUA()
    assert p.modo_nocturno is False
    assert p.filtro_luz is False


def test_preferencias_to_json_roundtrip():
    p = PreferenciasDUA(modo_nocturno=True, filtro_luz=True)
    raw = p.to_json()
    p2 = PreferenciasDUA.from_json(raw)
    assert p2.modo_nocturno is True
    assert p2.filtro_luz is True


def test_from_json_none_devuelve_defaults():
    p = PreferenciasDUA.from_json(None)
    assert p.modo_nocturno is False
    assert p.filtro_luz is False


def test_from_json_invalido_devuelve_defaults():
    p = PreferenciasDUA.from_json("esto no es json")
    assert p.modo_nocturno is False
    assert p.filtro_luz is False


def test_from_json_dict_parcial():
    p = PreferenciasDUA.from_json('{"modo_nocturno": true}')
    assert p.modo_nocturno is True
    assert p.filtro_luz is False
