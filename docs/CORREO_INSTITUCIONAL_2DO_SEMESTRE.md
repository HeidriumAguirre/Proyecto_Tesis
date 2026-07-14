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
- `CONTRATO_CONFIDENCIALIDAD_DATOS.docx` — documento de referencia descriptivo (marco legal, datos, derechos). **No se firma**, se usa como base para la conversación con los apoderados.
- `AUTORIZACION_TRATAMIENTO_DATOS.docx` — documento de **autorización firmable** por el colegio, la coordinadora PIE y el/la apoderado/a. Es el único que se firma.

---

## Mensajes diferenciados (cada destinatario con su párrafo propio)

Estimados Arnaldo, Carolina y Constanza:

Espero que se encuentren bien. Me permito escribirles en el marco del proyecto de tesis de Ingeniería Civil Informática que vengo desarrollando en la Universidad de Playa Ancha bajo la guía del Dr. Franklin Johnson, cuyo objetivo es validar un Sistema de Tutoría Inteligente (ITS) con arquitectura RAG para fortalecer el aprendizaje procedimental de matemática en estudiantes del Programa de Integración Escolar (PIE) del Colegio San Leonardo Murialdo de Valparaíso.

A partir de los hitos de validación sostenidos durante el primer semestre, me es grato compartir que el prototipo se encuentra **técnicamente operativo**: cuenta con autenticación diferenciada para estudiantes y docentes, entrada multimodal por texto y voz, reglas pedagógicas personalizadas según diagnóstico PIE (TEA, TDAH, DIL, DEA, DL), accesibilidad DUA (modo nocturno y filtro de luz cálida) y persistencia completa de sesiones en MySQL y ChromaDB.

Con el propósito de avanzar hacia la **etapa de pilotaje durante el segundo semestre 2026**, me permito solicitar formalmente su colaboración en las siguientes cuatro líneas de trabajo, cuya planificación detallada adjunto en la carta Gantt incluida en este correo:

## 1. Coordinación y obtención de autorizaciones

Propongo agendar una **reunión presencial de kickoff la segunda semana de agosto** (por confirmar fecha según su disponibilidad) para presentar el prototipo en funcionamiento, validar la carta Gantt y coordinar la logística de las reuniones de apoderados necesarias para obtener los consentimientos informados de participación de los estudiantes.

A estas reuniones asistiré personalmente con dos documentos impresos: el `CONTRATO_CONFIDENCIALIDAD_DATOS.docx` (para proyectar y explicar) y el `AUTORIZACION_TRATAMIENTO_DATOS.docx` (para que cada apoderado complete y firme al final). Carolina, si te parece bien, podemos definir un guion común de presentación de 5-10 minutos.

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

**Sobre los documentos jurídicos adjuntos** (importante para F1.3 — reuniones de apoderados): incluyo **dos documentos Word diferenciados**:

- `CONTRATO_CONFIDENCIALIDAD_DATOS.docx` es un **documento de referencia descriptivo** de 4 páginas. Resume el marco legal, los datos solicitados, las medidas de seguridad, los derechos del apoderado/a y las disposiciones finales. **No se firma**: sirve para que la Coordinadora PIE lo proyecte en las reuniones con los apoderados y resuelva dudas en base a él.

- `AUTORIZACION_TRATAMIENTO_DATOS.docx` es el **documento que sí se firma**. Es de 2 páginas, con un solo párrafo de autorización en primera persona, una declaración de haber leído el contrato, y los 4 bloques de firma (Investigadora, Representante del Colegio, Coordinadora PIE como testigo técnico, y Apoderado/a). Incluye ya mis datos de contacto como tesista (RUT 21.063.023-6, correo institucional, teléfono). El apoderado completa solo su nombre, RUT y nombre del estudiante, y firma.

Sugiero que en cada reunión con un apoderado, primero se proyecte el CONTRATO_CONFIDENCIALIDAD_DATOS (5-10 min explicando los puntos clave), se resuelvan dudas, y luego se pase a la firma del AUTORIZACION. El colegio queda con el original firmado de cada uno; yo me llevo una copia para archivar en la documentación de la tesis.

## 3. Pasantía en aula

Para documentar el contexto pedagógico real de uso, solicito autorización para realizar **observaciones no participantes en una clase de matemática de cada nivel** durante septiembre y octubre, con el objetivo de analizar las guías PIE vigentes y los factores de avance de los estudiantes. La pasantía será coordinada previamente con cada docente y no interferirá con el desarrollo normal de las clases. Cada visita tendrá una duración aproximada de una hora.

## 4. Pruebas del prototipo en reuniones presenciales

Una vez completados los pasos anteriores, el prototipo será demostrado **en reuniones presenciales de una hora** en el colegio, donde las docentes PIE y los estudiantes de apoyo podrán probar directamente el sistema. Para estas sesiones llevaré un kit portátil con la aplicación ya configurada y los datos de prueba cargados.

Las reuniones se coordinarían durante noviembre y diciembre, con un máximo de tres sesiones demostrativas. Al cierre de cada sesión se aplicará una **encuesta breve de satisfacción** para recoger feedback que permita ajustar el prototipo antes de la defensa de tesis.

## 5. Consultas específicas por destinatario

### Para Carolina Yáñez — Coordinación PIE

Carolina, dado que eres quien más conoce los perfiles PIE del colegio, te quisiera pedir orientación sobre un punto técnico del modelo de datos. En la base del prototipo tengo la siguiente tabla de diagnósticos (resumida):

```sql
INSERT INTO diagnostico (id_diagnostico, codigo, nombre_completo, descripcion) VALUES
  (UUID(), 'TEA',  'Trastorno del Espectro Autista',
   'Condicion del neurodesarrollo que afecta la comunicacion social y presenta patrones de conducta repetitivos.'),
  (UUID(), 'TDAH', 'Trastorno por Deficit de Atencion e Hiperactividad',
   'Condicion caracterizada por inatencion, hiperactividad e impulsividad que afecta el aprendizaje.'),
  (UUID(), 'DIL',  'Dificultad Intelectual Leve',
   'Funcionamiento intelectual significativamente por debajo del promedio con limitaciones en conducta adaptativa.'),
  (UUID(), 'DEA',  'Dificultad Especifica del Aprendizaje',
   'Dificultades persistentes en lectura, escritura o matematicas sin causa sensorial o intelectual aparente.'),
  (UUID(), 'DL',   'Dificultad del Lenguaje',
   'Alteracion en la adquisicion y desarrollo del lenguaje oral que impacta la comprension y expresion.');
```

Mi pregunta concreta: **¿podrías indicarme dónde o con quién del equipo PIE puedo corroborar que estas descripciones son técnicamente correctas y se ajustan a la nomenclatura que usa el colegio en sus informes?** No es necesario que las revises tú, basta con que me orientes hacia el especialista interno o el protocolo institucional que utiliza el Programa de Integración para validar la terminología antes de cargar los datos. Esto es clave para que la personalización del tutor socrático se base en descripciones clínicamente válidas y no en simplificaciones que puedan afectar la fidelidad del piloto.

### Para Arnaldo Maturana — Coordinación de Gestión Pedagógica

Arnaldo, en el F1.3 (reuniones con apoderados) y en el F4.3 (demos en reuniones) se requiere agendar bloques horarios. Te pediría apoyo para:

- **Coordinar las reuniones de consentimiento con los apoderados** de los 4 cursos en septiembre, idealmente agrupando las reuniones por jornada para minimizar la carga administrativa.
- **Aprobar el uso de las dependencias del colegio** (sala de reuniones, proyector, acceso a WiFi) para las 3 sesiones demostrativas de noviembre.

### Para Constanza Fernández — Profesora de Matemática / Profesora Jefe

Constanza, en el F3 (pasantía en aula) me sería muy útil contar con tu experiencia directa:

- **Acompañarme en al menos una visita de observación** a un curso de matemática donde haya estudiantes PIE. Tu mirada docente me ayudaría a interpretar las estrategias de andamiaje que observes y a validar que las recomendaciones del tutor socrático no entren en conflicto con la planificación anual de la asignatura.
- **Sugerir un problema real del libro o guía Mineduc** del nivel que visites, para usarlo como caso de prueba en el demo del F4. Con tu autorización, ese problema se cargaría a ChromaDB con metadatos del nivel y OA correspondiente.

Si alguna de estas solicitudes queda fuera de tu alcance, quedo abierta a ajustarla en la reunión de kickoff.

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
