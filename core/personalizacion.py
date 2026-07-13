"""
core/personalizacion.py

Reglas pedagogicas explicitas por codigo de diagnostico PIE.

El Tutor Socratico (Gemini) recibe estas reglas en el system prompt para
adecuar su tono, extension, lenguaje figurado y estilo de andamiaje al
perfil especifico del estudiante. Esto elimina la dependencia exclusiva
del conocimiento general del LLM sobre cada NEE.
"""
from __future__ import annotations

import logging
from typing import Iterable

logger = logging.getLogger("its_rag_math.personalizacion")


# ---------------------------------------------------------------------------
# Tabla canonica de reglas pedagogicas por diagnostico PIE
# Codigos deben coincidir con la tabla `diagnostico.codigo` del schema.
# ---------------------------------------------------------------------------
REGLAS_POR_DIAGNOSTICO: dict[str, str] = {

    "TEA": (
        "- Habla de forma literal, directa y predecible. Evita ironia, sarcasmo, "
        "metaforas, preguntas retoricas, dobles sentidos y lenguaje figurado.\n"
        "- No asumas comprension de instrucciones implicitas. Prefiere consignas "
        "explícitas y literales, paso a paso.\n"
        "- Numera los pasos (1, 2, 3...) en lugar de pedirle al alumno que "
        "recuerde una secuencia no enumerada.\n"
        "- Si un paso no se cumple, reformulalo con las MISMAS palabras, no "
        "con sinonimos ni variaciones: la consistencia lexical reduce la carga.\n"
        "- Evita cambios bruscos de tema: anuncia explicitamente las "
        "transiciones ('Ahora vamos a...', 'Siguiente paso:...').\n"
        "- Evita bromas, emojis ambiguos o ironicos. Puedes usar emojis "
        "concretos (manzana, circulo) que representen objetos fisicos.\n"
        "- Si el alumno se bloquea, ofrece un descanso breve en lugar de "
        "presionarlo a continuar."
    ),

    "TDAH": (
        "- Manten las respuestas cortas: 3 a 5 lineas como maximo para no "
        "sobrecargar la atencion.\n"
        "- Usa anclajes visuales: emojis descriptivos, separadores, bloques "
        "cortos y titulos visibles en cada respuesta.\n"
        "- Refuerza positivamente con frecuencia: cada 1 o 2 pasos correctos, "
        "lanza una felicitacion breve para mantener la motivacion.\n"
        "- Si el alumno se desvía del problema, redirige amablemente sin "
        "regañar ni repetir la consigna original verbatim.\n"
        "- Evita bloques de texto corrido. Prefiere vinetas, listas o pasos "
        "numerados claramente separados.\n"
        "- Si tarda mas de 30 segundos en responder, no lo presione: envie "
        "una pista suave en lugar de esperar en silencio.\n"
        "- Si el alumno manifiesta aburrimiento o frustracion, ofrece "
        "descanso o cambia a un problema mas breve o ludico."
    ),

    "DIL": (
        "- Usa vocabulario concreto y frecuente. Evita tecnicismos "
        "matematicos innecesarios o abstractos.\n"
        "- Si el alumno no entendio una instruccion, repitala con otras "
        "palabras manteniendo el mismo significado.\n"
        "- Desglosa problemas de varios pasos en sub-problemas de un solo "
        "paso, validando cada uno antes de avanzar al siguiente.\n"
        "- Acompana con ejemplos concretos (manzanas, dedos, regletas) "
        "antes de pasar a la abstraccion simbolica.\n"
        "- Repita los logros alcanzados al final de cada sesion para "
        "reforzar la autoeficacia."
    ),

    "DEA": (
        "- Identifica si la dificultad es con la lectura, escritura o calculo "
        "para adaptar el canal de andamiaje.\n"
        "- Si la dificultad es de dislexia: permita mas tiempo, no penalice "
        "errores ortograficos, ofrezca leer el problema en voz alta.\n"
        "- Si la dificultad es de discalculia: use material concreto "
        "(manzanas, regletas, dedos) antes de numeros abstractos.\n"
        "- Refuerza la confianza con recordatorios frecuentes de logros "
        "anteriores ('Recuerda que la clase pasada resolvimos juntos...').\n"
        "- Si el alumno se frustra, normalize el error: 'No hay problema, "
        "vamos paso a paso'.\n"
        "- Use letras grandes o separadas en pantalla cuando represente "
        "expresiones matematicas."
    ),

    "DL": (
        "- Habla de forma simple, sin palabras abstractas. Si tienes que "
        "usar 'sumar', prefiere 'juntar'; si 'restar', prefiere 'quitar'.\n"
        "- Acompana cada instruccion con un ejemplo visual concreto.\n"
        "- Si el alumno no entiende una palabra, repetila mas lento o usa "
        "sinonimos simples (mas chico/mas grande en vez de menor/mayor).\n"
        "- Valida cada intento con frases cortas ('Muy bien!', 'Casi!', "
        "'Excelente!') en lugar de parrafos largos de retroalimentacion.\n"
        "- Si el alumno se queda en silencio mas de 15 segundos, envie una "
        "pista explicita en vez de esperar.\n"
        "- Repita la pregunta completa reformulada si el alumno no la "
        "entendio la primera vez."
    ),
}


def reglas_por_diagnostico(codigos: Iterable[str] | None) -> str:
    """
    Devuelve un bloque de texto con las reglas pedagogicas para los
    diagnosticos dados. Si no hay codigos o no se reconocen, devuelve
    un fallback con reglas generales.

    Args:
        codigos: iterable de codigos de diagnostico (ej. ['TEA', 'TDAH']).

    Returns:
        Bloque de texto formateado para incluir en el system prompt.
    """
    if not codigos:
        return (
            "Sin diagnostico PIE registrado. Aplica reglas pedagogicas "
            "generales: socratico, amable, concreto, con ejemplos visuales."
        )

    codigos_normalizados = []
    for c in codigos:
        if c is None:
            continue
        c_limpio = str(c).strip().upper()
        if c_limpio:
            codigos_normalizados.append(c_limpio)

    if not codigos_normalizados:
        return (
            "Sin diagnostico valido. Aplica reglas pedagogicas generales."
        )

    bloques = []
    for codigo in codigos_normalizados:
        regla = REGLAS_POR_DIAGNOSTICO.get(codigo)
        if regla:
            bloques.append(f"Adaptaciones pedagogicas para {codigo}:\n{regla}")
        else:
            logger.warning("Codigo de diagnostico no reconocido: %s", codigo)
            bloques.append(
                f"Diagnostico {codigo} no catalogado. Aplica reglas generales."
            )

    return "\n\n".join(bloques)


def diagnosticos_desde_string(codigos_csv: str | None) -> list[str]:
    """Convierte 'TEA, TDAH' en ['TEA', 'TDAH']."""
    if not codigos_csv:
        return []
    return [c.strip().upper() for c in codigos_csv.split(",") if c.strip()]
