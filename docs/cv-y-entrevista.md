# Presentación del proyecto para CV y entrevista

## Título para el CV

**Proyecto personal · Topografía y control geométrico en O-PitBlast**

## Descripción breve

Caso de estudio con O-PitBlast 1.5.93.0: integración de una nube de 114 548 puntos y 153 referencias geométricas de taladros. Desarrollo de utilidades Python para trazabilidad, detección de duplicados y verificación de más de 228 mil caras, con pruebas automatizadas y documentación pública.

## Dos puntos para una sección de proyectos

- Verificación de una exportación topográfica mediante recuentos, hashes, tolerancias y conectividad; preservación de coordenadas y separación de un conjunto espacialmente incompatible.
- Documentación de importación y reapertura del proyecto nativo, con dos capturas seleccionadas, scripts reproducibles y límites de validación explícitos.

**Enlace:** https://github.com/casillagutierresmoises-del/opitblast-topografia-taladros

## Explicación de 45 segundos

> En este proyecto trabajé la integración de datos en O-PitBlast y su control geométrico. Había una nube topográfica, coordenadas de taladros y una malla de otra ubicación. Separé las procedencias y contrasté exportaciones con fuentes. El modelo local final conservó 114 548 puntos y se revisaron 228 439 caras. También documenté un problema de importación del relieve y otro de precisión numérica, preparando una referencia local reversible. La lectura del archivo guardado confirmó 153 referencias geométricas. Lo presento como una práctica de calidad de datos y manejo inicial del programa, con sus comprobaciones y límites visibles.

## Competencias demostradas

| Competencia | Evidencia |
| --- | --- |
| Lectura de datos mineros | Identificación de campos, separadores y procedencias. |
| Criterio geométrico | Separación de conjuntos incompatibles y preservación del relieve. |
| Trazabilidad | SHA-256 y cotejos entre entrada y exportación. |
| Programación aplicada | Dos utilidades Python y pruebas automatizadas. |
| Comunicación técnica | Memoria, resultados estructurados y evidencia seleccionada. |
| Uso de herramientas asistidas | Windows-MCP y asistencia de Codex documentados. |

## Preguntas que conviene poder explicar

1. ¿Por qué 114 548 puntos almacenados representan 114 259 posiciones únicas?
2. ¿Por qué no se combinó Malla Ejemplo con Terrain K?
3. ¿De dónde sale la tolerancia 0.0005 y qué no demuestra?
4. ¿Qué diferencia hay entre un patrón de diseño y la capa Floating Holes?
5. ¿Por qué una exportación anterior de 153 registros no acredita el recuento final de otra capa?

Las respuestas están en la memoria técnica. El repositorio acredita este proyecto personal y su método; no implica experiencia en campo, dominio integral del software, certificación del fabricante o relación laboral con una empresa.
