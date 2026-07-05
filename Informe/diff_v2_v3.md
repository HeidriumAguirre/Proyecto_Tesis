# Diff v2 -> v3: sincronizacion con el estado actual del prototipo

**Archivo base:** `Tesis_HeidriumAguirre_v2.docx`  
**Archivo nuevo:** `Tesis_HeidriumAguirre_v3.docx`  
**Cambios:** 9 parrafos ampliados, 5 parrafos insertados (RNF-8 a RNF-12), 2 tablas preservadas, Carta Gantt y Bibliografia intactas.

---

## Seccion 1 - Resumen ejecutivo (Tecnologico)

**Parrafo v2 (#36)** (579 chars):

> Desde el punto de vista tecnológico, el proyecto contemplará el desarrollo de un prototipo funcional utilizando el lenguaje de programación Python y el framework Streamlit como plataforma de interacción. Asimismo, incorporará un almacén vectorial para la recuperación semántica de información, un sistema de persistencia para registrar las interacciones de los usuarios y una interfaz diseñada bajo principios de accesibilidad y Diseño Universal para el Aprendizaje (DUA), considerando las necesidades propias de los estudiantes pertenecientes al Programa de Integración Escolar.

**Parrafo v3 (#36)** (1160 chars):

> Desde el punto de vista tecnológico, el proyecto contemplará el desarrollo de un prototipo funcional utilizando el lenguaje de programación Python y el framework Streamlit como plataforma de interacción. Asimismo, incorporará un almacén vectorial para la recuperación semántica de información, un sistema de persistencia para registrar las interacciones de los usuarios y una interfaz diseñada bajo principios de accesibilidad y Diseño Universal para el Aprendizaje (DUA), considerando las necesidades propias de los estudiantes pertenecientes al Programa de Integración Escolar. La arquitectura se orquestara mediante Docker y Docker Compose, lo que permitira declarar dos servicios desacoplados dentro de una red bridge dedicada: db_relacional (MySQL 8 con healthcheck, named volume mysql_data y schema.sql auto-cargado en /docker-entrypoint-initdb.d) y app_tutor (Streamlit 1.58 sobre python:3.11-slim con todas las dependencias pinneadas en requirements.txt). Esta capa de orquestacion garantizara portabilidad entre maquinas del equipo de desarrollo y reproducibilidad del entorno, ademas de aislar los servicios de infraestructura local del investigador.

**Texto anadido:**

```
 La arquitectura se orquestara mediante Docker y Docker Compose, lo que permitira declarar dos servicios desacoplados dentro de una red bridge dedicada: db_relacional (MySQL 8 con healthcheck, named volume mysql_data y schema.sql auto-cargado en /docker-entrypoint-initdb.d) y app_tutor (Streamlit 1.58 sobre python:3.11-slim con todas las dependencias pinneadas en requirements.txt). Esta capa de orquestacion garantizara portabilidad entre maquinas del equipo de desarrollo y reproducibilidad del entorno, ademas de aislar los servicios de infraestructura local del investigador.
```

---

## Seccion 1 - Resumen ejecutivo (Resultado)

**Parrafo v2 (#37)** (514 chars):

> Como resultado esperado, la investigación propondrá un Sistema de Tutoría Inteligente capaz de guiar al estudiante durante la resolución de problemas matemáticos mediante estrategias de tutoría socrática, retroalimentación personalizada y explicaciones fundamentadas en información curricular oficial, contribuyendo al fortalecimiento del aprendizaje procedimental y al desarrollo de una herramienta tecnológica de apoyo para docentes, estudiantes y equipos multidisciplinarios vinculados a la educación inclusiva.

**Parrafo v3 (#37)** (1292 chars):

> Como resultado esperado, la investigación propondrá un Sistema de Tutoría Inteligente capaz de guiar al estudiante durante la resolución de problemas matemáticos mediante estrategias de tutoría socrática, retroalimentación personalizada y explicaciones fundamentadas en información curricular oficial, contribuyendo al fortalecimiento del aprendizaje procedimental y al desarrollo de una herramienta tecnológica de apoyo para docentes, estudiantes y equipos multidisciplinarios vinculados a la educación inclusiva. El sistema incorporara autenticacion dual: los estudiantes ingresaran exclusivamente mediante su correo academico institucional previamente registrado por el educador PIE, mientras que los docentes accederan con correo y contrasena hasheada con bcrypt (rounds=12) con rate limit de cinco intentos fallidos cada quince minutos. La entrada del usuario aceptara tanto texto como voz: este ultimo canal utiliza la API multimodal de Gemini 2.5 Flash para transcribir el audio del estudiante y entregar la tutoria socratica. Finalmente, la interfaz ofrecera controles DUA persistentes por usuario: un modo nocturno completo y un filtro de luz calida ajustable de 0% a 100% mediante slider, reduciendo la fatiga visual y la sobreestimulacion sensorial en estudiantes neurodivergentes.

**Texto anadido:**

```
 El sistema incorporara autenticacion dual: los estudiantes ingresaran exclusivamente mediante su correo academico institucional previamente registrado por el educador PIE, mientras que los docentes accederan con correo y contrasena hasheada con bcrypt (rounds=12) con rate limit de cinco intentos fallidos cada quince minutos. La entrada del usuario aceptara tanto texto como voz: este ultimo canal utiliza la API multimodal de Gemini 2.5 Flash para transcribir el audio del estudiante y entregar la tutoria socratica. Finalmente, la interfaz ofrecera controles DUA persistentes por usuario: un modo nocturno completo y un filtro de luz calida ajustable de 0% a 100% mediante slider, reduciendo la fatiga visual y la sobreestimulacion sensorial en estudiantes neurodivergentes.
```

---

## Seccion 3.3 - Objetivo especifico (Prototipo)

**Parrafo v2 (#79)** (225 chars):

> Desarrollar un prototipo funcional que integre una arquitectura Retrieval-Augmented Generation con un modelo de lenguaje de gran escala para proporcionar tutoría personalizada durante la resolución de ejercicios matemáticos. 

**Parrafo v3 (#79)** (483 chars):

> Desarrollar un prototipo funcional que integre una arquitectura Retrieval-Augmented Generation con un modelo de lenguaje de gran escala para proporcionar tutoría personalizada durante la resolución de ejercicios matemáticos.  El prototipo se ejecutara como una aplicacion contenerizada, empaquetada en una imagen Docker basada en python:3.11-slim y orquestada con Docker Compose, e incluira autenticacion dual, entrada multimodal de voz y controles de accesibilidad DUA persistentes.

**Texto anadido:**

```
 El prototipo se ejecutara como una aplicacion contenerizada, empaquetada en una imagen Docker basada en python:3.11-slim y orquestada con Docker Compose, e incluira autenticacion dual, entrada multimodal de voz y controles de accesibilidad DUA persistentes.
```

---

## Seccion 3.4 - Producto tecnico (Prototipo Funcional)

**Parrafo v2 (#85)** (584 chars):

> Prototipo Funcional de Sistema de Tutoría Inteligente: Se desarrollará un prototipo funcional de un Sistema de Tutoría Inteligente implementado sobre el framework Streamlit, capaz de proporcionar acompañamiento personalizado durante la resolución de ejercicios matemáticos. La interfaz será diseñada considerando principios del Diseño Universal para el Aprendizaje (DUA), incorporando recursos que favorezcan la accesibilidad, la reducción de la carga cognitiva y la comprensión progresiva de las actividades por parte de estudiantes pertenecientes al Programa de Integración Escolar.

**Parrafo v3 (#85)** (1417 chars):

> Prototipo Funcional de Sistema de Tutoría Inteligente: Se desarrollará un prototipo funcional de un Sistema de Tutoría Inteligente implementado sobre el framework Streamlit, capaz de proporcionar acompañamiento personalizado durante la resolución de ejercicios matemáticos. La interfaz será diseñada considerando principios del Diseño Universal para el Aprendizaje (DUA), incorporando recursos que favorezcan la accesibilidad, la reducción de la carga cognitiva y la comprensión progresiva de las actividades por parte de estudiantes pertenecientes al Programa de Integración Escolar. El despliegue se realizara mediante una pila Docker Compose que declara un servicio db_relacional (MySQL 8.0 con volumen nombrado para persistencia y healthcheck que bloquea el arranque del frontend hasta confirmar disponibilidad) y un servicio app_tutor construido desde un Dockerfile propio, con usuario no-root (appuser), certificados TLS autofirmados generados con mkcert para habilitar HTTPS (requisito indispensable para que el navegador autorice la captura de microfono requerida por la entrada de voz) y healthcheck HTTPS propio. El esquema relacional se inicializara automaticamente al primer arranque del contenedor MySQL mediante el archivo data/schema.sql montado en /docker-entrypoint-initdb.d/, incluyendo el usuario docente semilla con clave hasheada y los datos de prueba necesarios para la validacion del prototipo.

**Texto anadido:**

```
 El despliegue se realizara mediante una pila Docker Compose que declara un servicio db_relacional (MySQL 8.0 con volumen nombrado para persistencia y healthcheck que bloquea el arranque del frontend hasta confirmar disponibilidad) y un servicio app_tutor construido desde un Dockerfile propio, con usuario no-root (appuser), certificados TLS autofirmados generados con mkcert para habilitar HTTPS (requisito indispensable para que el navegador autorice la captura de microfono requerida por la entrada de voz) y healthcheck HTTPS propio. El esquema relacional se inicializara automaticamente al primer arranque del contenedor MySQL mediante el archivo data/schema.sql montado en /docker-entrypoint-initdb.d/, incluyendo el usuario docente semilla con clave hasheada y los datos de prueba necesarios para la validacion del prototipo.
```

---

## Seccion 3.4 - Producto tecnico (ChromaDB)

**Parrafo v2 (#86)** (473 chars):

> Base de Conocimiento Curricular mediante Almacén Vectorial: Se implementará una base de conocimiento basada en un almacén vectorial (ChromaDB), construida a partir de documentación oficial del Ministerio de Educación de Chile correspondiente al primer ciclo de Educación Básica. Este componente permitirá realizar búsquedas semánticas sobre Bases Curriculares, Programas de Estudio y otros recursos pedagógicos utilizados por el sistema durante la generación de respuestas.

**Parrafo v3 (#86)** (921 chars):

> Base de Conocimiento Curricular mediante Almacén Vectorial: Se implementará una base de conocimiento basada en un almacén vectorial (ChromaDB), construida a partir de documentación oficial del Ministerio de Educación de Chile correspondiente al primer ciclo de Educación Básica. Este componente permitirá realizar búsquedas semánticas sobre Bases Curriculares, Programas de Estudio y otros recursos pedagógicos utilizados por el sistema durante la generación de respuestas. Los vectores se persistiran en disco dentro del contenedor de la aplicacion y se montaran en un named volume de Docker (chroma_data), lo que evitara la perdida de embeddings tras un eventual rebuild de la imagen. Adicionalmente, la coleccion de ChromaDB y el cliente del modelo de lenguaje se almacenaran en memoria mediante @st.cache_resource de Streamlit, protegiendo la RAM del host al evitar reinicializaciones por cada rerun de la aplicacion.

**Texto anadido:**

```
 Los vectores se persistiran en disco dentro del contenedor de la aplicacion y se montaran en un named volume de Docker (chroma_data), lo que evitara la perdida de embeddings tras un eventual rebuild de la imagen. Adicionalmente, la coleccion de ChromaDB y el cliente del modelo de lenguaje se almacenaran en memoria mediante @st.cache_resource de Streamlit, protegiendo la RAM del host al evitar reinicializaciones por cada rerun de la aplicacion.
```

---

## Seccion 3.4 - Producto tecnico (Persistencia)

**Parrafo v2 (#88)** (387 chars):

> Sistema de Persistencia y Seguimiento de Aprendizaje: Se implementará un sistema de persistencia utilizando una base de datos relacional que permitirá almacenar las sesiones de tutoría, el historial de interacciones y el progreso de cada estudiante. Esta información facilitará el seguimiento del proceso de aprendizaje y permitirá futuras funcionalidades asociadas al monitoreo docente.

**Parrafo v3 (#88)** (1200 chars):

> Sistema de Persistencia y Seguimiento de Aprendizaje: Se implementará un sistema de persistencia utilizando una base de datos relacional que permitirá almacenar las sesiones de tutoría, el historial de interacciones y el progreso de cada estudiante. Esta información facilitará el seguimiento del proceso de aprendizaje y permitirá futuras funcionalidades asociadas al monitoreo docente. El sistema de persistencia se implementa sobre MySQL 8 con charset utf8mb4 (soporte completo para tildes, enie y emojis) y motor InnoDB, ejecutandose como contenedor dentro del compose. El modelo de datos contempla trece tablas: las de dominio (usuario, estudiante_pie, diagnostico, sesion_tutoria, recurso_mineduc, plan_adaptacion, sugerencia_pedagogica), las de perfilado PIE (estudiante_diagnostico, objetivo_aprendizaje) y las de soporte al flujo docente, a saber, intento_login para aplicar rate limit a la autenticacion, auditoria_docente para registrar la trazabilidad de cada operacion CRUD del educador PIE con timestamp y detalle en formato JSON, y la columna deleted_at en usuario y estudiante_pie para implementar soft delete preservando el historial academico y clinico de los estudiantes retirados.

**Texto anadido:**

```
 El sistema de persistencia se implementa sobre MySQL 8 con charset utf8mb4 (soporte completo para tildes, enie y emojis) y motor InnoDB, ejecutandose como contenedor dentro del compose. El modelo de datos contempla trece tablas: las de dominio (usuario, estudiante_pie, diagnostico, sesion_tutoria, recurso_mineduc, plan_adaptacion, sugerencia_pedagogica), las de perfilado PIE (estudiante_diagnostico, objetivo_aprendizaje) y las de soporte al flujo docente, a saber, intento_login para aplicar rate limit a la autenticacion, auditoria_docente para registrar la trazabilidad de cada operacion CRUD del educador PIE con timestamp y detalle en formato JSON, y la columna deleted_at en usuario y estudiante_pie para implementar soft delete preservando el historial academico y clinico de los estudiantes retirados.
```

---

## RNF-1 (v2 original = RNF generico 1)

**Parrafo v2 (#217)** (126 chars):

> Presentar una interfaz intuitiva y de fácil utilización para estudiantes de primero a cuarto año de Educación General Básica. 

**Parrafo v3 (#217)** (393 chars):

> RNF-1 Rendimiento: El sistema debera mantener tiempos de respuesta iniciales inferiores a tres segundos durante la interaccion con el estudiante, logrados mediante una ventana deslizante de los ultimos seis turnos enviada al modelo de lenguaje y mediante el uso de @st.cache_resource de Streamlit para preservar en memoria las conexiones a MySQL, el cliente de ChromaDB y el cliente de Gemini.

**Cambio completo** (texto original reemplazado).

---

## RNF-2 (v2 original = RNF generico 2)

**Parrafo v2 (#218)** (82 chars):

> Mantener tiempos de respuesta adecuados durante la interacción con el estudiante. 

**Parrafo v3 (#218)** (267 chars):

> RNF-2 Proteccion de memoria: La coleccion vectorial de ChromaDB, el cliente del SDK generativo y la conexion a MySQL deberan almacenarse en cache de recursos de Streamlit, evitando reinicializaciones costosas en cada rerun y protegiendo la RAM del host de desarrollo.

**Cambio completo** (texto original reemplazado).

---

## RNF-3 (v2 original = RNF generico 3)

**Parrafo v2 (#219)** (74 chars):

> Garantizar la persistencia y disponibilidad de la información almacenada. 

**Parrafo v3 (#219)** (285 chars):

> RNF-3 Persistencia vectorial: Los embeddings generados por ChromaDB deberan almacenarse en disco dentro del contenedor y montarse en un named volume de Docker (chroma_data), de modo que sobrevivan al rebuild de la imagen y puedan respaldarse mediante los mecanismos estandar de Docker.

**Cambio completo** (texto original reemplazado).

---

## RNF-4 (v2 original = RNF generico 4)

**Parrafo v2 (#220)** (129 chars):

> Favorecer la escalabilidad de la arquitectura para incorporar nuevas asignaturas y contenidos curriculares en futuras versiones. 

**Parrafo v3 (#220)** (261 chars):

> RNF-4 Persistencia relacional: El motor de base de datos MySQL 8 debera ejecutarse como servicio del compose (db_relacional) con named volume mysql_data y charset utf8mb4 para garantizar soporte completo de caracteres en espanol chileno (tildes, enie) y emojis.

**Cambio completo** (texto original reemplazado).

---

## RNF-5 (v2 original = RNF generico 5)

**Parrafo v2 (#221)** (114 chars):

> Considerar criterios de accesibilidad orientados a estudiantes pertenecientes al Programa de Integración Escolar. 

**Parrafo v3 (#221)** (311 chars):

> RNF-5 Resiliencia de red: Las conexiones a MySQL deberan implementar reintentos automaticos con backoff exponencial (mediante la libreria tenacity) y verificacion ping-reconnect, tolerando microcortes producidos durante el reinicio del contenedor db_relacional o latencia transitoria de la red bridge de Docker.

**Cambio completo** (texto original reemplazado).

---

## RNF-6 (v2 original = RNF generico 6)

**Parrafo v2 (#222)** (130 chars):

> Implementar una arquitectura modular que facilite el mantenimiento, actualización y reutilización de los componentes del sistema. 

**Parrafo v3 (#222)** (320 chars):

> RNF-6 Seguridad de credenciales: Las contrasenas del educador PIE deberan almacenarse hasheadas con bcrypt rounds=12, jamas en texto plano. El sistema debera aplicar rate limit de cinco intentos fallidos en quince minutos por correo, persistiendo cada intento en la tabla intento_login para auditoria y bloqueo temporal.

**Cambio completo** (texto original reemplazado).

---

## RNF-7 (v2 original = RNF generico 7)

**Parrafo v2 (#223)** (118 chars):

> Resguardar la integridad de la información almacenada y controlar el acceso a los distintos módulos de la aplicación. 

**Parrafo v3 (#223)** (343 chars):

> RNF-7 Trazabilidad PIE: Toda operacion CRUD realizada por un docente sobre un estudiante (crear, editar, eliminar, cerrar sesion, abandonar sesion) debera registrarse en la tabla auditoria_docente con timestamp, accion y detalle en formato JSON, asegurando la trazabilidad exigida por los marcos normativos del Programa de Integracion Escolar.

**Cambio completo** (texto original reemplazado).

---

## Seccion 9.2 - Metodologia (Implementacion)

**Parrafo v2 (#233)** (551 chars):

> Durante la fase de implementación se desarrollará el prototipo utilizando el lenguaje de programación Python y el framework Streamlit. Se integrarán los distintos componentes tecnológicos necesarios para el funcionamiento del sistema, incluyendo el almacén vectorial ChromaDB, la base de datos MySQL y el modelo de lenguaje seleccionado para la generación de respuestas. La integración de estos componentes permitirá construir una plataforma capaz de recuperar información curricular relevante y generar tutorías contextualizadas para cada estudiante.

**Parrafo v3 (#238)** (1403 chars):

> Durante la fase de implementación se desarrollará el prototipo utilizando el lenguaje de programación Python y el framework Streamlit. Se integrarán los distintos componentes tecnológicos necesarios para el funcionamiento del sistema, incluyendo el almacén vectorial ChromaDB, la base de datos MySQL y el modelo de lenguaje seleccionado para la generación de respuestas. La integración de estos componentes permitirá construir una plataforma capaz de recuperar información curricular relevante y generar tutorías contextualizadas para cada estudiante. La fase de implementacion contemplara la construccion de una imagen Docker basada en python:3.11-slim, con inclusion de la libreria libgomp1 requerida por ChromaDB, instalacion del codigo como usuario no-root (appuser) y exposicion del servicio sobre HTTPS con certificados TLS autofirmados generados con mkcert. La aplicacion sera orquestada con Docker Compose, declarando dos servicios en una red bridge dedicada (db_relacional para MySQL y app_tutor para Streamlit) con healthcheck que bloquea el arranque del frontend hasta confirmar la disponibilidad de la base de datos, asegurando asi la inicializacion ordenada del sistema. Ademas, se incorporara la entrada de voz mediante la API multimodal de Gemini 2.5 Flash, lo que requerira la inclusion de un certificado HTTPS valido para que el navegador autorice el acceso al microfono del estudiante.

**Texto anadido:**

```
 La fase de implementacion contemplara la construccion de una imagen Docker basada en python:3.11-slim, con inclusion de la libreria libgomp1 requerida por ChromaDB, instalacion del codigo como usuario no-root (appuser) y exposicion del servicio sobre HTTPS con certificados TLS autofirmados generados con mkcert. La aplicacion sera orquestada con Docker Compose, declarando dos servicios en una red bridge dedicada (db_relacional para MySQL y app_tutor para Streamlit) con healthcheck que bloquea el arranque del frontend hasta confirmar la disponibilidad de la base de datos, asegurando asi la inicializacion ordenada del sistema. Ademas, se incorporara la entrada de voz mediante la API multimodal de Gemini 2.5 Flash, lo que requerira la inclusion de un certificado HTTPS valido para que el navegador autorice el acceso al microfono del estudiante.
```

---

## Seccion 9.3 - Planificacion (Diseno/Implementacion)

**Parrafo v2 (#241)** (442 chars):

> La tercera etapa corresponderá al diseño e implementación del prototipo funcional. En ella se desarrollarán los distintos módulos del Sistema de Tutoría Inteligente, incluyendo la interfaz de usuario, la integración del modelo de lenguaje, el almacén vectorial para la recuperación semántica de información, la base de datos relacional y los mecanismos de persistencia necesarios para registrar el historial de aprendizaje de los estudiantes.

**Parrafo v3 (#246)** (781 chars):

> La tercera etapa corresponderá al diseño e implementación del prototipo funcional. En ella se desarrollarán los distintos módulos del Sistema de Tutoría Inteligente, incluyendo la interfaz de usuario, la integración del modelo de lenguaje, el almacén vectorial para la recuperación semántica de información, la base de datos relacional y los mecanismos de persistencia necesarios para registrar el historial de aprendizaje de los estudiantes. Esta etapa incluira el empaquetado de la aplicacion en una imagen Docker reproducible, versionada mediante el archivo requirements.txt con dependencias pinneadas, y desplegada a traves de un archivo docker-compose.yml que declara los servicios necesarios, los volumenes nombrados para persistencia y las politicas de reinicio ante fallos.

**Texto anadido:**

```
 Esta etapa incluira el empaquetado de la aplicacion en una imagen Docker reproducible, versionada mediante el archivo requirements.txt con dependencias pinneadas, y desplegada a traves de un archivo docker-compose.yml que declara los servicios necesarios, los volumenes nombrados para persistencia y las politicas de reinicio ante fallos.
```

---

## Listado de los 12 RNFs finales (v3)

- **Parrafo 217**: RNF-1 Rendimiento: El sistema debera mantener tiempos de respuesta iniciales inferiores a tres segundos durante la interaccion con el estudiante, logrados mediante una ventana deslizante de los ultimos seis turnos enviada al modelo de lenguaje y mediante el uso de @st.cache_resource de Streamlit para preservar en memoria las conexiones a MySQL, el cliente de ChromaDB y el cliente de Gemini.

- **Parrafo 218**: RNF-2 Proteccion de memoria: La coleccion vectorial de ChromaDB, el cliente del SDK generativo y la conexion a MySQL deberan almacenarse en cache de recursos de Streamlit, evitando reinicializaciones costosas en cada rerun y protegiendo la RAM del host de desarrollo.

- **Parrafo 219**: RNF-3 Persistencia vectorial: Los embeddings generados por ChromaDB deberan almacenarse en disco dentro del contenedor y montarse en un named volume de Docker (chroma_data), de modo que sobrevivan al rebuild de la imagen y puedan respaldarse mediante los mecanismos estandar de Docker.

- **Parrafo 220**: RNF-4 Persistencia relacional: El motor de base de datos MySQL 8 debera ejecutarse como servicio del compose (db_relacional) con named volume mysql_data y charset utf8mb4 para garantizar soporte completo de caracteres en espanol chileno (tildes, enie) y emojis.

- **Parrafo 221**: RNF-5 Resiliencia de red: Las conexiones a MySQL deberan implementar reintentos automaticos con backoff exponencial (mediante la libreria tenacity) y verificacion ping-reconnect, tolerando microcortes producidos durante el reinicio del contenedor db_relacional o latencia transitoria de la red bridge de Docker.

- **Parrafo 222**: RNF-6 Seguridad de credenciales: Las contrasenas del educador PIE deberan almacenarse hasheadas con bcrypt rounds=12, jamas en texto plano. El sistema debera aplicar rate limit de cinco intentos fallidos en quince minutos por correo, persistiendo cada intento en la tabla intento_login para auditoria y bloqueo temporal.

- **Parrafo 223**: RNF-7 Trazabilidad PIE: Toda operacion CRUD realizada por un docente sobre un estudiante (crear, editar, eliminar, cerrar sesion, abandonar sesion) debera registrarse en la tabla auditoria_docente con timestamp, accion y detalle en formato JSON, asegurando la trazabilidad exigida por los marcos normativos del Programa de Integracion Escolar.

- **Parrafo 224**: RNF-8 HTTPS obligatorio: La aplicacion debera exponerse exclusivamente sobre HTTPS utilizando certificados TLS autofirmados generados con la herramienta mkcert, ya que los navegadores modernos exigen un contexto seguro para habilitar la API getUserMedia() que requiere el componente de captura de voz del sistema.

- **Parrafo 225**: RNF-9 Aislamiento y seguridad del contenedor: La aplicacion debera ejecutarse como usuario no-root (appuser) dentro del contenedor, limitando las dependencias del sistema operativo a paquetes esenciales como libgomp1, requerido por hnswlib para el indice vectorial de ChromaDB.

- **Parrafo 226**: RNF-10 Accesibilidad DUA: La interfaz debera ofrecer un modo nocturno completo y un filtro de luz calida ajustable de 0% a 100% mediante slider, reduciendo la fatiga visual y la sobreestimulacion sensorial en estudiantes neurodivergentes. Las preferencias de cada usuario deberan persistirse en el campo preferencias_dua (JSON) de las tablas usuario y estudiante_pie.

- **Parrafo 227**: RNF-11 Reproducibilidad del entorno: Las dependencias de Python deberan instalarse con versiones pinneadas en el archivo requirements.txt (Streamlit, ChromaDB, google-genai, bcrypt, tenacity, langchain-community, entre otras), garantizando que la imagen Docker resultante sea reproducible entre distintos entornos de desarrollo.

- **Parrafo 228**: RNF-12 Modularidad: El codigo debera organizarse en nucleos funcionales independientes (core/config, core/auth, core/admin, core/dua, core/llm, core/prompts, core/retries), lo que facilitara el mantenimiento, la realizacion de pruebas unitarias y la reutilizacion de componentes en futuras iteraciones del proyecto.

---

## Validacion de integridad

- Total de parrafos v2: 309
- Total de parrafos v3: 314
- Total de tablas v2: 2
- Total de tablas v3: 2
- Carta Gantt presente: True
- Bibliografia presente: True
- Total de RNFs: 12

