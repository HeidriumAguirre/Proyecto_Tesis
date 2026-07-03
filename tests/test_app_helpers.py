"""
Smoke tests para los helpers de LLM (sin tocar Streamlit ni MySQL).
"""
from core.llm import separar_transcripcion_y_respuesta, construir_contexto_ventana


def test_separar_transcripcion_y_respuesta_exitoso():
    crudo = "TRANSCRIPCION: Hola profesor\n\nRESPUESTA: Hola! Como estas?"
    t, r = separar_transcripcion_y_respuesta(crudo)
    assert t == "Hola profesor"
    assert r == "Hola! Como estas?"


def test_separar_sin_marcador():
    crudo = "Solo una respuesta sin marcadores."
    t, r = separar_transcripcion_y_respuesta(crudo)
    assert t == ""
    assert r == "Solo una respuesta sin marcadores."


def test_construir_contexto_ventana_acota_turnos():
    messages = [{"role": "user", "content": f"turno {i}"} for i in range(20)]
    contexto = construir_contexto_ventana(messages, ventana=6)
    # Solo los ultimos 6 turnos (14..19)
    assert "turno 14" in contexto
    assert "turno 19" in contexto
    assert "turno 0" not in contexto
    assert "turno 13" not in contexto


def test_construir_contexto_ventana_menos_de_ventana():
    messages = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    contexto = construir_contexto_ventana(messages, ventana=6)
    assert "Alumno: a" in contexto
    assert "Tutor Socratico: b" in contexto
