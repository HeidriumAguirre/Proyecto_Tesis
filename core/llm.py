"""
Helpers de logica del LLM (separables de Streamlit para testeo).
"""
from __future__ import annotations

VENTANA_CONTEXTO_TURNOS = 6


def construir_contexto_ventana(messages: list[dict], ventana: int = VENTANA_CONTEXTO_TURNOS) -> str:
    """Construye el contexto tomando solo los ultimos N turnos."""
    recientes = messages[-ventana:] if len(messages) > ventana else messages
    lineas = []
    for m in recientes:
        if m["role"] == "user":
            lineas.append(f"Alumno: {m['content']}")
        else:
            lineas.append(f"Tutor Socratico: {m['content']}")
    return "\n".join(lineas)


def separar_transcripcion_y_respuesta(texto_llm: str) -> tuple[str, str]:
    """Parsea la respuesta del LLM multimodal: 'TRANSCRIPCION: ... RESPUESTA: ...'."""
    marcador = "RESPUESTA:"
    if marcador in texto_llm:
        head, tail = texto_llm.split(marcador, 1)
        transcripcion = head.replace("TRANSCRIPCION:", "").strip()
        return transcripcion, tail.strip()
    return "", texto_llm.strip()
