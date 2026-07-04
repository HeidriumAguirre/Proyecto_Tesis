"""
Tests para core.admin (badges y modelos).
No requieren conexion a MySQL.
"""
from core.admin import SesionTutoria, badge_html, COLOR_POR_ESTADO


def test_badge_html_contiene_color_y_emoji():
    html = badge_html("Activa")
    assert "Activa" in html
    assert "#FFD700" in html
    assert "🟡" in html


def test_badge_html_estado_desconocido():
    html = badge_html("EstadoInventado")
    assert "#888888" in html


def test_sesion_tutoria_from_row():
    row = {
        "id_sesion": "abc-123",
        "id_estudiante": "est-1",
        "curso_subdivision": "A",
        "fecha_inicio": "2026-07-03 14:00:00",
        "fecha_fin": None,
        "estado_sesion": "Activa",
    }
    s = SesionTutoria.from_row(row)
    assert s.id_sesion == "abc-123"
    assert s.curso_subdivision == "A"
    assert s.estado_sesion == "Activa"
    assert s.fecha_fin is None


def test_color_por_estado_tiene_los_tres_estados():
    assert "Activa" in COLOR_POR_ESTADO
    assert "Completada" in COLOR_POR_ESTADO
    assert "Abandonada" in COLOR_POR_ESTADO
