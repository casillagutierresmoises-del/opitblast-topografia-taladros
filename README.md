# Terrain K · Topografía y control geométrico en O-PitBlast

**Caso de estudio académico y técnico · O-PitBlast 1.5.93.0 · Python · Calidad de datos**

Integración de una nube topográfica y coordenadas de taladros, con trazabilidad desde los archivos de origen hasta las evidencias del programa. El proyecto combina manejo de software minero con comprobaciones reproducibles de geometría.

## Problema y resultado

El taller reúne archivos que parecen relacionados, pero **no todos corresponden a la misma ubicación**. Además, una importación de taladros puede sustituir el relieve por una superficie de collares. El trabajo consiste en conservar coordenadas y procedencia, incorporar el conjunto compatible y comprobar el resultado.

Se recuperó el relieve de Terrain K, se incorporó la capa `Floating Holes` sobre ese terreno y se guardó y volvió a abrir el proyecto nativo. La verificación del terreno contrasta sus puntos y conectividad. La capa final de taladros tiene comprobación visual; su recuento nativo final permanece pendiente.

| Resultado medido | Valor |
| --- | ---: |
| Puntos topográficos conservados | 114 548 |
| Posiciones XYZ únicas / repeticiones | 114 259 / 289 |
| Triángulos exportados y revisados | 228 438 |
| Error máximo del cotejo de coordenadas | 0.0000037841796875 |
| Tolerancia según exportación de tres decimales | 0.0005 |
| Registros de origen de Floating Holes | 153 |
| Puntos de Malla Ejemplo mantenidos aparte | 195 |

Las cifras son controles de los archivos y exportaciones; no representan precisión de un levantamiento en campo. Las unidades y el sistema de referencia no están declarados en las fuentes.

## Dos vistas del resultado

**Vista general del relieve y la distribución de taladros flotantes**

![Vista general de Terrain K en O-PitBlast](media/capturas/vista-general.png)

**Detalle del banco y los segmentos de Floating Holes**

![Detalle del terreno y Floating Holes](media/capturas/detalle-3d.png)

Capturas reales de O-PitBlast. Los segmentos oscuros corresponden a una capa de referencia geométrica; no acreditan un diseño nuevo de perforación.

## Desarrollo técnico

1. Identificación de la versión y respaldo del proyecto nativo.
2. Inspección de campos, separadores, coordenadas, duplicados y hashes.
3. Extracción DXF → CSV XYZ conservando cadenas decimales, orden y repeticiones.
4. Importación del relieve y cotejo de su exportación nativa.
5. Importación específica de `Floating Holes`, con seis coordenadas de boca y fondo.
6. Guardado, reapertura y documentación de las comprobaciones y sus límites.

Se detectaron y separaron los 195 registros de `Malla Ejemplo`, cuyas coordenadas pertenecen a otro conjunto. No se desplazaron para hacerlos coincidir.

## Explorar el proyecto

| Documento | Contenido |
| --- | --- |
| [Memoria técnica](docs/memoria-tecnica.md) | Problema, decisiones, resultados, criterios de aceptación y límites. |
| [Flujo en O-PitBlast](docs/flujo-inicial.md) | Pasos de la sesión, mapeo e importadores. |
| [Comprobación de datos](docs/verificacion-datos.md) | Evidencia numérica y distinción entre etapas. |
| [Reproducir las verificaciones](docs/uso-reproducible.md) | Comandos, requisitos, códigos de salida y pruebas. |
| [Resultados estructurados](docs/resultados-fuentes.json) | Recuentos, hashes, tolerancias y estado del proyecto. |
| [Descripción para CV y entrevista](docs/cv-y-entrevista.md) | Presentación breve del trabajo y competencias demostradas. |

## Ejecutar las pruebas

Requiere **Python 3.10 o posterior** y su biblioteca estándar. No instala dependencias.

```sh
python -m unittest discover -s tests -v
```

Las pruebas usan archivos sintéticos temporales. Los originales del taller y el proyecto `.opit` se conservan localmente; el repositorio publica documentación, código y dos capturas.

## Alcance

Este caso cubre topografía, importación y calidad geométrica. Quedan documentadas la ausencia de CRS y unidades certificadas, la falta de propiedades de los taladros y la comprobación exclusivamente visual de la capa final Floating Holes. No constituye un plan operativo de voladura.

**Herramientas:** O-PitBlast 1.5.93.0, Python, inspección auxiliar con ezdxf y asistencia de Codex mediante la skill local y [Windows-MCP](https://github.com/CursorTouch/Windows-MCP). El control de interfaz es general de Windows; no es una API interna del fabricante. Proyecto personal sin afiliación al fabricante ni a una empresa minera.
