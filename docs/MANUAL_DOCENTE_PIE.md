# Manual Docente PIE — Sistema de Tutoría Inteligente (ITS)

**Proyecto de Tesis — Ingeniería Civil Informática — Universidad de Playa Ancha**
**Colegio San Leonardo Murialdo — Valparaíso**
**Versión 1.0 — Piloto 2do semestre 2026**

---

**Alcance del piloto**: 4 estudiantes mínimo (uno por nivel: 1° a 4° básico), idealmente con diagnósticos PIE distintos. Si más apoderados se suman voluntariamente, el alcance se ampliará proporcionalmente.

## 1. Acceso al sistema

Abra su navegador y vaya a la URL que le fue indicada por la tesista.
Recomendamos usar **Google Chrome** o **Microsoft Edge** actualizados.

### 1.1 Inicio de sesión (docente PIE)

En la pantalla inicial verá dos pestañas:

| Pestaña | Quién la usa | Cómo ingresar |
|---|---|---|
| 👤 Estudiante / Persona de apoyo | Alumnos PIE | Solo correo académico institucional |
| 🧑‍🏫 Docente PIE | Educadores | Correo **+ contraseña** |

**Su correo es el institucional** que la universidad asignó a la tesista (ejemplo: `amaturana@murialdovalpo.cl`).
La contraseña inicial se le entregó por correo al iniciar el piloto. **Cámbiela** al primer ingreso desde la opción "Recuperar contraseña" (próximamente).

> ⚠️ Si escribe mal la contraseña 5 veces en 15 minutos, el sistema bloquea su cuenta por seguridad durante 15 minutos.

---

## 2. Panel del docente

Una vez autenticado, el panel se divide en **cuatro bloques** en la columna principal y opciones en la **barra lateral izquierda**.

### 2.1 Barra lateral (sidebar)

```
🏫 Colegio Murialdo
  │
  ├── 🎨 Accesibilidad DUA
  │     ├── 🌙 Modo Nocturno  (activar/desactivar)
  │     └── 🔅 Filtro de Luz Nocturna  (slider 0-100%)
  │
  └── Sesión actual
        ├── Su nombre y rol
        └── 🚪 Cerrar sesión
```

#### 🌙 Modo Nocturno
Reduce la fatiga visual. Recomendado para sesiones largas de revisión de datos. **Su preferencia se guarda automáticamente**.

#### 🔅 Filtro de Luz Nocturna (slider 0-100%)
Aplica un tinte cálido a la pantalla, similar al filtro Night Shift de Apple. Recomendado:
- 0-30%: uso diurno normal
- 50-70%: sesiones vespertinas
- 80-100%: estudiantes con sensibilidad sensorial alta (TEA, TDAH)

### 2.2 Pestañas por nivel (1° a 4° Básico)

En la columna principal, seleccione el curso. Cada pestaña tiene un **selector A/B** para elegir la subdivisión del curso.

### 2.3 Lista de alumnos

Por cada alumno verá:

| Campo | Significado |
|---|---|
| **Nombre completo** | Tal como fue registrado |
| **📧 Correo** | Con el que el alumno inicia sesión |
| **Adaptación: Alto/Medio/Bajo** | Determina el lenguaje del tutor |
| ✏️ (icono lápiz) | Editar perfil |
| 🗑️ (icono papelera) | Eliminar (soft delete, conserva historial) |

### 2.4 Botón "+ Agregar alumno"

Al hacer clic se abre un formulario con los campos:

| Campo | Obligatorio | Ejemplo |
|---|---|---|
| RUT anonimizado | ✅ | `99.999.999-9` |
| Nombre completo | ✅ | `Nombre Apellido Apellido` |
| Correo académico | ⚠️ (recomendado) | `iniciales@murialdo.cl` |
| Curso | ✅ (pre-rellenado) | 1° a 4° Básico |
| Subdivisión | ✅ (pre-rellenado) | A o B |
| Nivel de adaptación | ✅ | Alto / Medio / Bajo |
| ☑ Requiere apoyo pictórico | opcional | Use emojis de manzanas en respuestas |
| Diagnósticos (multi-select) | opcional | TEA, TDAH, DIL, DEA, DL |

**Importante**: el alumno **no ve su diagnóstico** en pantalla. Esos datos solo los usa el tutor IA internamente para adaptar su lenguaje.

### 2.5 Sesiones recientes

A la derecha de la lista de alumnos verá un panel con las últimas sesiones:

| Color | Estado | Significado |
|---|---|---|
| 🟡 Amarillo | **Activa** | El alumno está usando el tutor ahora mismo |
| 🟢 Verde | **Completada** | El docente la cerró o pasaron 30 min sin actividad |
| 🔴 Rojo | **Abandonada** | Cerrada manualmente como abandonada |

**Acciones disponibles**:
- ✅ **Cerrar** (sesión activa → completada)
- 🔴 **Abandonar** (sesión activa → abandonada, para análisis posterior)

---

## 3. Cómo funciona la Tutoría Socrática (para entender qué ve el alumno)

Cuando un alumno escribe o habla, el sistema:

1. Lee su perfil de la BD (diagnóstico + nivel + pictórico)
2. Busca en los documentos oficiales del Mineduc el contenido relevante
3. Envía a Gemini 2.5 Flash un **prompt personalizado** que incluye:
   - Las **reglas pedagógicas** específicas para su diagnóstico (TEA, TDAH, etc.)
   - Su nivel de lenguaje (Alto/Medio/Bajo)
   - Si requiere apoyo pictórico
   - El fragmento curricular encontrado
4. El tutor responde siguiendo el **método socrático**: hace preguntas en vez de dar la respuesta directa.

**Ejemplo de personalización**:

| Alumno | Diagnóstico | Lo que hace el tutor |
|---|---|---|
| Mateo | TEA, nivel Alto | "Cuenta conmigo: ¿cuántas 🍎 tienes? Ahora regálale 4 a tu primo. ¿Cuántas te quedan?" (pasos numerados, lenguaje literal) |
| Sofía | TDAH, nivel Medio | "¡Bien! Ahora intenta este." (respuestas cortas, refuerzo positivo) |
| Lucas | DEA, nivel Bajo | "Vamos paso a paso. ¿Puedes leer este problema en voz alta?" (canal concreto) |

---

## 4. Privacidad y resguardo de datos

En cumplimiento del **Decreto Supremo 170/2009** y el **Decreto Exento 83/2015** del Ministerio de Educación:

- ✅ Los alumnos **NO ven** su diagnóstico, nivel de adaptación, ni requieren pictórico.
- ✅ Todas las acciones del docente quedan registradas en la tabla `auditoria_docente` (qué hizo, cuándo, sobre qué alumno).
- ✅ Los datos personales reales **nunca se ingresan al sistema**. Se usan RUTs anonimizados y nombres de pila.
- ✅ Si elimina un alumno, su historial **se preserva** (soft delete), pero deja de aparecer en las listas activas.
- ✅ Solo la tesista (Heidrium Aguirre) tiene acceso administrativo completo.

---

## 5. Solución de problemas

| Problema | Solución |
|---|---|
| No puedo iniciar sesión | Verificar que el correo sea el institucional. Si la contraseña no funciona, contactar a la tesista. |
| El micrófono no graba | Verificar que el navegador tenga permiso de micrófono. Requiere HTTPS (ya configurado). |
| Un alumno no aparece en la lista | Verificar que el curso y subdivisión seleccionados coincidan con los del alumno. |
| El sistema está lento | El sistema usa caché para conexiones. Si pasa, refrescar el navegador (Ctrl+Shift+R). |
| No escucho al tutor (TTS) | El tutor tiene un botón "🔊 Escuchar a Sócrates" en cada respuesta. Hacer clic para que el navegador lo lea en voz alta. |
| Olvidé la contraseña | Por ahora, contactar directamente a la tesista para reset. |

---

## 6. Contacto y soporte

**Tesista**: Heidrium Aguirre Andrades
**Email**: heidrium.aguirre@alumnos.upla.cl
**Profesor guía**: Dr. Franklin Johnson
**Institución**: Universidad de Playa Ancha — Ingeniería Civil Informática

Para consultas técnicas o reportar problemas durante el piloto, escribir directamente a la tesista con:
- Captura de pantalla del error
- Pasos para reproducir
- Navegador y sistema operativo usado

---

*Manual generado en el marco de la tesis de pregrado. Versión 1.0 — Julio 2026.*
