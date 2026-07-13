"""
Tests para core.personalizacion.
Validan que las reglas pedagogicas son distintas para cada diagnostico
y que la funcion maneja correctamente los casos borde.
"""
from core.personalizacion import (
    REGLAS_POR_DIAGNOSTICO,
    diagnosticos_desde_string,
    reglas_por_diagnostico,
)


def test_regras_por_diagnostico_tiene_los_5_codigos_pie():
    """El catalogo debe cubrir los 5 diagnosticos PIE del seed."""
    assert set(REGLAS_POR_DIAGNOSTICO.keys()) == {"TEA", "TDAH", "DIL", "DEA", "DL"}


def test_cada_diagnostico_tiene_reglas_no_vacias():
    """Ningun diagnostico debe tener reglas vacias o triviales."""
    for codigo, reglas in REGLAS_POR_DIAGNOSTICO.items():
        assert len(reglas) > 50, f"{codigo} tiene reglas muy cortas"


def test_reglas_son_distintas_entre_diagnosticos():
    """Las reglas de TEA y TDAH no pueden ser identicas (obvio si son distintos)."""
    assert REGLAS_POR_DIAGNOSTICO["TEA"] != REGLAS_POR_DIAGNOSTICO["TDAH"]
    assert REGLAS_POR_DIAGNOSTICO["DIL"] != REGLAS_POR_DIAGNOSTICO["DL"]
    assert REGLAS_POR_DIAGNOSTICO["DEA"] != REGLAS_POR_DIAGNOSTICO["TEA"]


def test_reglas_tea_contienen_palabras_clave():
    """Las reglas de TEA deben mencionar palabras clave del perfil TEA."""
    reglas = REGLAS_POR_DIAGNOSTICO["TEA"].lower()
    assert "literal" in reglas or "directa" in reglas
    assert "metafor" in reglas or "iron" in reglas or "figurad" in reglas
    assert "predecible" in reglas or "consistencia" in reglas


def test_reglas_tdah_contienen_palabras_clave():
    """Las reglas de TDAH deben mencionar palabras clave del perfil TDAH."""
    reglas = REGLAS_POR_DIAGNOSTICO["TDAH"].lower()
    assert "cortas" in reglas or "atencion" in reglas
    assert "ancla" in reglas or "visual" in reglas or "emoji" in reglas
    assert "felicita" in reglas or "refuerza" in reglas


def test_reglas_por_diagnostico_con_codigos_validos():
    texto = reglas_por_diagnostico(["TEA"])
    assert "Adaptaciones pedagogicas para TEA" in texto
    assert "literal" in texto


def test_reglas_por_diagnostico_con_multiples_codigos():
    texto = reglas_por_diagnostico(["TEA", "TDAH"])
    assert "Adaptaciones pedagogicas para TEA" in texto
    assert "Adaptaciones pedagogicas para TDAH" in texto


def test_reglas_por_diagnostico_sin_codigos():
    texto = reglas_por_diagnostico(None)
    assert "Sin diagnostico" in texto


def test_reglas_por_diagnostico_lista_vacia():
    texto = reglas_por_diagnostico([])
    assert "Sin diagnostico" in texto


def test_reglas_por_diagnostico_codigo_desconocido():
    """Un codigo no catalogado debe generar fallback, no crashear."""
    texto = reglas_por_diagnostico(["XYZ_FAKE"])
    assert "no catalogado" in texto.lower() or "reglas generales" in texto.lower()


def test_diagnosticos_desde_string_csv():
    """Convierte 'TEA, TDAH' en lista limpia."""
    assert diagnosticos_desde_string("TEA, TDAH") == ["TEA", "TDAH"]
    assert diagnosticos_desde_string("tea,t dah") == ["TEA", "T DAH"]
    assert diagnosticos_desde_string(None) == []
    assert diagnosticos_desde_string("") == []
    assert diagnosticos_desde_string("TEA,,,") == ["TEA"]


def test_system_instruction_incluye_bloque_diagnostico():
    """Verifica que el prompt del tutor ahora incluye las reglas del diagnostico."""
    from core.prompts import system_instruction_socratico
    prompt = system_instruction_socratico(
        nombre="Mateo Test",
        diagnosticos="TEA",
        nivel_adaptacion="Alto",
        requiere_apoyo_pictorico=True,
        contexto_pedagogico="contexto de prueba",
    )
    assert "Adaptaciones pedagogicas para TEA" in prompt
    assert "literal" in prompt


def test_system_instruction_con_multiples_diagnosticos():
    """Prompt con TEA + TDAH debe incluir ambos bloques."""
    from core.prompts import system_instruction_socratico
    prompt = system_instruction_socratico(
        nombre="Alumno Test",
        diagnosticos="TEA, TDAH",
        nivel_adaptacion="Medio",
        requiere_apoyo_pictorico=False,
        contexto_pedagogico="",
    )
    assert "Adaptaciones pedagogicas para TEA" in prompt
    assert "Adaptaciones pedagogicas para TDAH" in prompt


def test_system_instruction_sin_diagnostico():
    """Sin diagnosticos debe caer al fallback, no fallar."""
    from core.prompts import system_instruction_socratico
    prompt = system_instruction_socratico(
        nombre="Alumno Test",
        diagnosticos="",
        nivel_adaptacion="Alto",
        requiere_apoyo_pictorico=True,
        contexto_pedagogico="",
    )
    assert "Sin diagnostico" in prompt
    # Las reglas socraticas base siempre presentes
    assert "REGLAS DE ORO SOCRATICAS" in prompt
