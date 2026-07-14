# Contrato de Confidencialidad y Autorización de Tratamiento de Datos

**Proyecto**: Sistema de Tutoría Inteligente (ITS) basado en RAG para el fortalecimiento del aprendizaje procedimental y la inclusión NEE en Educación Básica Municipal

**Tesista**: Heidrium Nauj Aguirre Andrades — Ingeniería Civil Informática — Universidad de Playa Ancha

**Profesor guía**: Dr. Franklin Johnson — Universidad de Playa Ancha

**Versión**: 1.0 — Julio 2026

---

> **Documento de referencia para mostrar en reuniones con apoderados.**
> Este archivo describe **qué datos se tratarán, con qué fines, bajo qué medidas de seguridad y qué derechos asisten al apoderado/a**. Para firmar la autorización, ver el documento `AUTORIZACION_TRATAMIENTO_DATOS.docx`.

---

## 1. Antecedentes y marco normativo

El presente contrato se suscribe en el marco del proyecto de tesis de pregrado señalado, y se rige por las siguientes disposiciones legales y reglamentarias chilenas:

- **Ley N.° 19.628** sobre Protección de la Vida Privada y Protección de Datos de Carácter Personal.
- **Decreto Supremo N.° 170/2009** del Ministerio de Educación, que fija normas para determinar los alumnos con necesidades educativas especiales que serán beneficiarios de la subvención educacional especial, y en particular sus disposiciones sobre confidencialidad de la información.
- **Decreto Exento N.° 83/2015** del Ministerio de Educación, que aprueba criterios y orientaciones de adecuación curricular para estudiantes con NEE.
- **Ley N.° 20.422** sobre Igualdad de Oportunidades e Inclusión Social de Personas con Discapacidad.
- **Constitución Política de Chile**, artículo 19 N.° 4 (derecho a la vida privada) y N.° 24 (derecho de propiedad sobre datos personales).

---

## 2. Objeto del contrato

Autorizar formalmente el tratamiento de **datos anonimizados de 4 estudiantes del Programa de Integración Escolar (PIE)** del Colegio San Leonardo Murialdo de Valparaíso, con el único fin de validar académicamente el prototipo de Sistema de Tutoría Inteligente en el marco del proyecto de tesis indicado.

---

## 3. Partes

### 3.1 Investigadora (responsable del tratamiento)
La responsable del tratamiento es la **tesista de Ingeniería Civil Informática de la Universidad de Playa Ancha** que ejecuta el proyecto. Sus datos identificativos completos (nombre, RUT, correo institucional y teléfono) figuran en el documento de autorización adjunto.

### 3.2 Establecimiento educacional (custodio de los datos originales)
El **Colegio San Leonardo Murialdo de Valparaíso** actúa como custodio de los datos identificativos reales de los estudiantes, a través de su representante legal y de la **Coordinadora PIE** del establecimiento. Los datos identificativos completos del colegio y su representante figuran en el documento de autorización adjunto.

### 3.3 Apoderado/a (autorizante del estudiante)
Es la persona natural que firma la autorización adjunta, en calidad de representante legal del estudiante PIE que participa en el piloto. Sus datos identificativos figuran en el mismo documento.

---

## 4. Naturaleza y alcance de los datos tratados

### 4.1 Datos que se solicitan al colegio (anonimizados)

| Categoría | Campo específico | Tratamiento |
|---|---|---|
| Identificación | RUT anonimizado (ficticio, formato XX.XXX.XXX-X) | Reemplazo del RUT real por uno generado aleatoriamente |
| Identificación | Nombre de pila (solo nombre y primer apellido) | Seudonimización parcial |
| Académica | Curso y subdivisión (A o B) | Tal cual |
| Académica | Nivel de adaptación de lenguaje (Alto, Medio, Bajo) | Tal cual |
| Pedagógica | Requiere apoyo pictórico (Sí/No) | Tal cual |
| Clínica (PIE) | Códigos de diagnóstico (TEA, TDAH, DIL, DEA, DL) | Tal cual |

### 4.2 Datos que NO se solicitarán bajo ninguna circunstancia

- RUT real del estudiante.
- Nombre completo del estudiante.
- Dirección domiciliaria.
- Datos de salud no contenidos en la categoría PIE (fichas clínicas, medicamentos, diagnósticos médicos no PIE).
- Antecedentes familiares.
- Datos de contacto del estudiante o su familia.
- Fotografías, grabaciones de voz o video.
- Información sobre rendimiento escolar específico (calificaciones, asistencia).
- Orientación sexual, religión, origen étnico u otra información sensible.

### 4.3 Datos generados durante el piloto

Durante el uso del prototipo se generará información de **interacción pedagógica** que se almacenará en la base de datos del sistema:

- Mensajes escritos o transcritos de audio intercambiados con el tutor socrático.
- Fecha, hora y duración de cada sesión.
- Objetivo de aprendizaje (OA) consultado en cada sesión.
- Métricas agregadas (número de sesiones, preguntas realizadas, duración promedio).

Estos datos se conservarán **únicamente mientras dure el proyecto de tesis** y se eliminarán al cierre del mismo (estimado marzo 2027), con excepción de los resúmenes estadísticos agregados que puedan incluirse en la memoria de título.

---

## 5. Finalidad del tratamiento

Los datos descritos en el punto 4 se utilizarán **exclusivamente** para:

1. Cargar perfiles PIE anonimizados en la base de datos del prototipo.
2. Personalizar las respuestas del tutor socrático según el diagnóstico y nivel del estudiante.
3. Validar la personalización del tutor mediante demostración a docentes PIE (sin mostrar datos clínicos).
4. Analizar métricas agregadas de uso para la memoria de título de pregrado.
5. Publicar resultados agregados y anonimizados en la memoria de tesis y eventuales publicaciones académicas derivadas.

**Queda expresamente prohibido**:

- Re-identificar a los estudiantes a partir de los datos anonimizados.
- Compartir los datos con terceros no involucrados en el proyecto.
- Usar los datos con fines comerciales, publicitarios o de vigilancia.
- Difundir datos individuales (solo se publicarán métricas agregadas).

---

## 6. Medidas de seguridad y resguardo

La investigadora se compromete a aplicar las siguientes medidas:

- **Anonimización previa** de todos los datos antes de cargarlos al sistema.
- **Acceso restringido** a la base de datos (solo la tesista y su profesor guía).
- **Contraseñas robustas** (mínimo 12 caracteres, alfanuméricas, con símbolos) para todos los accesos.
- **No publicación de datos identificables** en la memoria de tesis, repositorios públicos (GitHub), o presentaciones.
- **Cifrado de la base de datos** en tránsito (HTTPS) y en reposo (volúmenes Docker cifrados a nivel de host).
- **Eliminación definitiva** de los datos al cierre del proyecto, salvo los resúmenes estadísticos agregados.
- **Bitácora de auditoría** de todas las acciones realizadas sobre los datos.

---

## 7. Compromisos del colegio

El Colegio San Leonardo Murialdo, a través de su representante legal y de la Coordinadora PIE, se compromete a:

1. Entregar los datos **estrictamente anonimizados** según la plantilla `PLANTILLA_INGESTA_ESTUDIANTES.csv` proporcionada por la investigadora.
2. No entregar datos identificables reales bajo ninguna circunstancia.
3. Informar a los apoderados sobre el presente contrato y obtener su firma antes de la entrega de datos.
4. Custodiar el original firmado del contrato de cada apoderado.
5. Respetar el derecho del apoderado a **retirar el consentimiento** en cualquier momento, sin represalias para el estudiante.
6. Coordinar con la investigadora cualquier solicitud de acceso, rectificación o eliminación de datos.

---

## 8. Derechos del apoderado/a y del estudiante

Conforme a la Ley N.° 19.628, el apoderado y el estudiante tienen los siguientes derechos:

- **Acceso**: conocer qué datos se tratan y para qué fin.
- **Rectificación**: corregir datos inexactos.
- **Cancelación**: solicitar la eliminación de los datos del sistema.
- **Oposición**: oponerse a un tratamiento específico.
- **Revocación del consentimiento**: retirar el consentimiento otorgado en cualquier momento.

Estos derechos se ejercen mediante solicitud escrita dirigida a la investigadora al correo `heidrium.aguirre@alumnos.upla.cl`, quien deberá responder en un plazo máximo de **10 días hábiles**.

---

## 9. Duración y revocación

El presente contrato tendrá una duración **indefinida hasta el cierre del proyecto de tesis** (estimado marzo 2027). El apoderado podrá revocar el consentimiento en cualquier momento mediante comunicación escrita a la investigadora o al colegio.

En caso de revocación, los datos del estudiante serán **eliminados en un plazo máximo de 30 días** desde la recepción de la solicitud, manteniendo solo los resúmenes estadísticos agregados ya generados (que no permiten re-identificación).

---

## 10. Confidencialidad de las partes

Las partes firmantes se obligan a mantener la **más estricta confidencialidad** sobre:

- Datos identificables de los estudiantes.
- Diagnósticos clínicos específicos asociados a un estudiante.
- Cualquier información que pudiera permitir re-identificar a un estudiante.

Esta obligación se mantiene **vigente aún después de finalizado el proyecto** y tiene carácter indefinido.

---

## 11. Solución de controversias

Cualquier controversia derivada del presente contrato será resuelta preferentemente por **acuerdo directo** entre las partes. En caso de no alcanzarse acuerdo, las partes se someten a la competencia de los **Tribunales Ordinarios de Justicia de Valparaíso**, Chile.

---

## 12. Disposiciones finales

- El presente contrato se firma en **3 ejemplares** del mismo tenor, quedando uno en poder de cada parte (investigadora, colegio, apoderado).
- La **firma del apoderado** es requisito habilitante para que el estudiante participe del piloto.
- La **firma del colegio** formaliza la autorización institucional.
- La **firma de la investigadora** declara el compromiso de cumplimiento.

---

**Versión 1.0** — Julio 2026
**Documento elaborado en el marco del proyecto de tesis de pregrado en Ingeniería Civil Informática, Universidad de Playa Ancha.**

---

## Anexo A — Resumen para el apoderado (1 carilla)

Cuando se reúna a los apoderados, basta con entregarles este resumen (1 carilla) antes de pedirles firma en el contrato completo:

> **CONSENTIMIENTO INFORMADO — Resumen**
>
> Su hijo/a es parte de un piloto educativo del Colegio San Leonardo Murialdo junto a la Universidad de Playa Ancha. En este piloto se prueba un tutor digital de matemáticas que se adapta al diagnóstico PIE de cada estudiante.
>
> **¿Qué datos entregaremos?**
> Solo el código del diagnóstico PIE (por ejemplo, TEA, TDAH), el nivel de adaptación de lenguaje y un RUT ficticio para identificar al alumno en el sistema. No entregaremos el RUT real, ni nombre completo, ni dirección, ni datos clínicos.
>
> **¿Para qué se usarán?**
> Para que el tutor digital entregue respuestas adaptadas a su hijo/a durante las sesiones de prueba, y para escribir la tesis de pregrado de la estudiante Heidrium Aguirre.
>
> **¿Puedo retirarme?**
> Sí, en cualquier momento y sin consecuencias para su hijo/a. Solo escríbale a la investigadora.
>
> **¿Quién verá los datos?**
> Solo la estudiante tesista y su profesor guía de universidad. No se compartirán con terceros.
>
> Para más detalles, lea el **Contrato de Confidencialidad** completo disponible con la Coordinadora PIE.

---

*Fin del documento.*
