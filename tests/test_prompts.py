"""
Tests para el modulo core.prompts.
Validan que el system instruction se adapte al perfil PIE.
"""
from core.prompts import system_instruction_socratico, REGLAS_SOCRATICAS_BASE


def test_system_instruction_incluye_nombre_y_diagnostico():
    instr = system_instruction_socratico(
        nombre="Mateo Gonzalez",
        diagnosticos="TEA",
        nivel_adaptacion="Alto",
        requiere_apoyo_pictorico=True,
        contexto_pedagogico="Contexto de prueba",
    )
    assert "Mateo Gonzalez" in instr
    assert "TEA" in instr
    assert "MUY simples" in instr
    assert "apoyo pictorico" in instr.lower()
    assert REGLAS_SOCRATICAS_BASE.split("\n")[0] in instr


def test_system_instruction_sin_apoyo_pictorico():
    instr = system_instruction_socratico(
        nombre="Alumno X",
        diagnosticos="TDAH",
        nivel_adaptacion="Medio",
        requiere_apoyo_pictorico=False,
        contexto_pedagogico="",
    )
    assert "TDAH" in instr
    # Si no requiere pictorico, NO debe decir "requiere apoyo pictorico"
    assert "requiere apoyo pictorico" not in instr.lower()
    assert "Sin contexto pedagogico" in instr


def test_nivel_bajo_no_mensaje_alto():
    instr = system_instruction_socratico(
        nombre="Alumno Y",
        diagnosticos="TEA",
        nivel_adaptacion="Bajo",
        requiere_apoyo_pictorico=False,
        contexto_pedagogico="",
    )
    # Si el nivel es Bajo, no debe mencionar reglas del nivel Alto
    assert "MUY simples" not in instr
