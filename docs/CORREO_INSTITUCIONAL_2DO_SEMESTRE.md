# Correo institucional — 2do semestre 2026

**Asunto**: Coordinación 2do semestre – Piloto Sistema de Tutoría Inteligente PIE (Tesis Ing. Civil Informática)

**De**: Heidrium Aguirre Andrades <heidrium.aguirre@alumnos.upla.cl>
**Para**:
- Arnaldo Maturana (Coordinador de Gestión Pedagógica) <amaturana@murialdovalpo.cl>
- Carolina Yáñez (Coordinadora PIE) <cyanez@murialdovalpo.cl>
- Constanza Fernández (Profesora de Matemática / Profesora Jefe) <constanzafernandez@murialdovalpo.cl>

**CC**: Dr. Franklin Johnson (Profesor Guía) <fjohnson@upla.cl>

**Adjuntos**:
- `Carta_Gantt_2do_Semestre_2026.pdf` — cronograma detallado
- `PLANTILLA_INGESTA_ESTUDIANTES.csv` — formato de los datos solicitados
- `Tesis_HeidriumAguirre_v3.docx` — estado actual del prototipo

---

Estimados Arnaldo, Carolina y Constanza:

Espero que se encuentren bien. Me permito escribirles en el marco del proyecto de tesis de Ingeniería Civil Informática que vengo desarrollando en la Universidad de Playa Ancha bajo la guía del Dr. Franklin Johnson, cuyo objetivo es validar un Sistema de Tutoría Inteligente (ITS) con arquitectura RAG para fortalecer el aprendizaje procedimental de matemática en estudiantes del Programa de Integración Escolar (PIE) del Colegio San Leonardo Murialdo de Valparaíso.

A partir de los hitos de validación sostenidos durante el primer semestre, me es grato compartir que el prototipo se encuentra **técnicamente operativo**: cuenta con autenticación diferenciada para estudiantes y docentes, entrada multimodal por texto y voz, reglas pedagógicas personalizadas según diagnóstico PIE (TEA, TDAH, DIL, DEA, DL), accesibilidad DUA (modo nocturno y filtro de luz cálida) y persistencia completa de sesiones en MySQL y ChromaDB.

Con el propósito de avanzar hacia la **etapa de pilotaje durante el segundo semestre 2026**, me permito solicitar formalmente su colaboración en las siguientes cuatro líneas de trabajo, cuya planificación detallada adjunto en la carta Gantt incluida en este correo:

## 1. Coordinación y obtención de autorizaciones

Propongo agendar una **reunión presencial de kickoff la segunda semana de agosto** (por confirmar fecha según su disponibilidad) para presentar el prototipo en funcionamiento, validar la carta Gantt y coordinar la logística de las reuniones de apoderados necesarias para obtener los consentimientos informados de participación de los estudiantes.

## 2. Set de datos anonimizados para la demo

En el marco del **Decreto Supremo N.° 170/2009** y el **Decreto Exento N.° 83/2015**, que regulan el resguardo de datos de estudiantes con Necesidades Educativas Especiales, solicito formalmente la entrega de un **set de fichas anonimizadas** de los estudiantes PIE del colegio.

**Alcance mínimo acordado con el colegio**: un estudiante por nivel, es decir, **4 estudiantes en total (uno de 1° Básico, uno de 2°, uno de 3° y uno de 4°)**, idealmente con **diagnósticos PIE distintos** (TEA, TDAH, DEA, DL, etc.) para validar la personalización del tutor. Si más apoderados se suman voluntariamente, el alcance se ampliará proporcionalmente.

Adjunto a este correo encontrarán el archivo **`PLANTILLA_INGESTA_ESTUDIANTES.csv`** con la estructura exacta esperada y 4 filas de ejemplo. Las columnas requeridas son:

| Columna | Descripción | Ejemplo |
|---|---|---|
| `rut_anonimizado` | RUT ficticio (formato XX.XXX.XXX-X) | `11.111.111-1` |
| `nombre_pila` | Solo nombre y primer apellido | `Alumno A` |
| `correo_academico` | Correo institucional del alumno | `alumno.a@murialdo.cl` |
| `curso` | 1_Basico, 2_Basico, 3_Basico o 4_Basico | `1_Basico` |
| `curso_subdivision` | A o B | `A` |
| `nivel_adaptacion` | Alto, Medio o Bajo | `Alto` |
| `requiere_apoyo_pictorico` | 1 (sí) o 0 (no) | `1` |
| `codigos_diagnostico` | TEA, TDAH, DIL, DEA o DL (separados por \|) | `TEA` o `TEA\|TDAH` |

Los datos serán tratados conforme a la **Ley N.° 19.628 sobre Protección de Datos Personales** y utilizados únicamente para fines de validación académica del prototipo.

## 3. Pasantía en aula

Para documentar el contexto pedagógico real de uso, solicito autorización para realizar **observaciones no participantes en una clase de matemática de cada nivel** durante septiembre y octubre, con el objetivo de analizar las guías PIE vigentes y los factores de avance de los estudiantes. La pasantía será coordinada previamente con cada docente y no interferirá con el desarrollo normal de las clases. Cada visita tendrá una duración aproximada de una hora.

## 4. Pruebas del prototipo en reuniones presenciales

Una vez completados los pasos anteriores, el prototipo será demostrado **en reuniones presenciales de una hora** en el colegio, donde las docentes PIE y los estudiantes de apoyo podrán probar directamente el sistema. Para estas sesiones llevaré un kit portátil con la aplicación ya configurada y los datos de prueba cargados.

Las reuniones se coordinarían durante noviembre y diciembre, con un máximo de tres sesiones demostrativas. Al cierre de cada sesión se aplicará una **encuesta breve de satisfacción** para recoger feedback que permita ajustar el prototipo antes de la defensa de tesis.

## Próximos pasos

Quedo a su disposición para agendar la reunión de coordinación en la fecha que mejor les resulte. Para avanzar, sugiero el siguiente orden:

1. **Respuesta a este correo** confirmando recepción y disponibilidad para la reunión de kickoff (segunda semana de agosto).
2. **Reunión presencial** donde presentaré el demo en vivo y entregaremos los consentimientos para los apoderados.
3. **Entrega del archivo CSV anonimizado** con los 4 alumnos durante septiembre (F2.2).
4. **Coordinación de fechas de pasantía** durante septiembre-octubre.

Agradezco profundamente la disposición y el apoyo que el Colegio Murialdo ha brindado a este proyecto desde sus inicios, el cual representa una contribución concreta al desarrollo de la educación inclusiva en nuestra región.

Saludos cordiales,

---

**Heidrium Nauj Aguirre Andrades**
Tesista de Ingeniería Civil Informática
Universidad de Playa Ancha
Email: heidrium.aguirre@alumnos.upla.cl
Teléfono: +56 X XXXX XXXX

**Dirigido por**: Dr. Franklin Johnson
Profesor Guía — Universidad de Playa Ancha
