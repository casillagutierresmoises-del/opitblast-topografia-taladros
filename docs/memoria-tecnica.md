# Memoria técnica · Terrain K

**Versión del caso:** 1.0 · **Fecha:** 6 de noviembre de 2026
**Entorno:** O-PitBlast 1.5.93.0 en Windows; utilidades Python 3.10+.

## Objetivo

Construir un caso trazable de integración y control geométrico: preservar una nube topográfica, identificar datos de otra ubicación y contrastar una exportación nativa antes de documentar el resultado del software.

El entregable reúne un proyecto `.opit` local, evidencia visual seleccionada, informes numéricos, dos utilidades de línea de comandos y pruebas automatizadas. Permite evaluar el método y sus resultados sin disponer de una licencia del programa para leer la documentación.

## Fuentes y compatibilidad

| Archivo | Datos disponibles | Decisión |
| --- | --- | --- |
| Terrain K - Cloud 2.dxf | DXF R12/AC1009; 114 548 POINT en CLOUD_001; XYZ explícitos. | Conjunto topográfico principal. |
| Floating Holes.csv | 153 registros; XYZ de boca y fondo; collar Z=98. | Incorporar como capa de referencia mediante Floating Holes. |
| Malla Ejemplo.csv | 195 ID únicos y coordenadas ESTE, NORTE, ELEV; elevación 3645. | Mantener separado por incompatibilidad espacial y ausencia de fondo. |

Los collares de Floating Holes están dentro de la caja XY de Terrain K. Es un control de compatibilidad inicial: por sí solo no demuestra un CRS común, exactitud del levantamiento o correspondencia física en campo.

Las cajas XY de Malla Ejemplo y Terrain K son disjuntas. No se combinaron, trasladaron ni completaron con profundidades ausentes. La separación conserva su procedencia.

## Método

### Identidad y preservación

Se contrastó la versión del ejecutable completo del taller y se guardó una copia previa del proyecto. Las fuentes se leyeron sin editarlas. Los informes identifican cada archivo mediante nombre y SHA-256; no publican rutas personales.

### Preparación de la nube

El DXF contiene puntos, sin caras. Se extrajeron los grupos explícitos 10, 20 y 30 de las entidades POINT en ENTITIES. La copia CSV conserva las cadenas decimales del origen, el orden y los puntos repetidos. No se reasignan ejes ni se convierten unidades.

La extracción reproducida genera **7 778 868 bytes** y SHA-256:

```text
9023dd94103cc00f8d1297981cdfcea3e7f04a358b6a1ce77692a4e971b39e23
```

El conversor publicado está limitado a DXF ASCII con POINT explícitos. No resuelve bloques, inserciones, superficies, transformaciones ni otros tipos de geometría CAD.

### Importación y control del relieve

Se incorporó el CSV XYZ mediante el importador de terreno. Después se exportaron puntos y caras desde el programa y se contrastaron con la nube de entrada. El cotejo considera la precisión de tres decimales del CSV exportado.

La exportación inicial conserva los 114 548 puntos, incluidos 289 repetidos. Sus 228 438 caras referencian todas las 114 259 posiciones XYZ únicas. Los 289 registros sin referencia son redundantes; no son ubicaciones topográficas únicas omitidas.

### Coordenadas de taladros

Una prueba anterior mediante Import Pattern produjo un CSV de 153 registros cuyas seis coordenadas coinciden exactamente con la fuente. Esa prueba también evidenció una superficie plana construida desde los collares. Se restauró el relieve original y se verificó de nuevo.

La incorporación usa **Boreholes → Floating Holes → Import** y el mapeo X, Y, Z, X_TOE, Y_TOE, Z_TOE. Esta herramienta representa una capa de referencia, diferente de un patrón de diseño nuevo. El primer proyecto se guardó y volvió a abrir con terreno y segmentos visibles.

El cotejo numérico de Import Pattern no se atribuye a Floating Holes. Para cerrar el recuento de esta capa se realizó una lectura estructural del `.opit` con `System.Formats.Nrbf`, sin deserializar objetos de O-PitBlast. Tanto el primer archivo como el final contienen 153 referencias y 153 geometrías distintas. Esta lectura no es una exportación de la aplicación ni una API del fabricante.

### Diagnóstico de precisión y referencia local

La geometría examinada contiene componentes `System.Single`. La primera importación mostró diferencias globales reconstruidas máximas de 0.050500732421875 en X y 0.4419974975585938 en Y. Una conversión de coordenadas globales a precisión simple antes de restar un origen reproduce las 153 filas, pero la secuencia interna es una **inferencia numérica**, no una conclusión sobre el código del fabricante.

Se prepararon copias restando el mismo mínimo XYZ del terreno a todos sus puntos y a los dos extremos de cada referencia. Se empleó `Decimal` de precisión 60; la inversión, el orden, los duplicados y las diferencias vectoriales se comprobaron sin modificar las fuentes. El origen completo y la fórmula inversa están en [Precisión de coordenadas](precision-coordenadas.md).

El archivo `TerrainK_Geometria_Local.opit` conserva 114 548 puntos y 153 referencias distintas. Las 153 filas concuerdan con el modelo de conversión a `Single` después de trasladar a la referencia local. La máxima diferencia reconstruida queda en 0.000003723144535 en X y 0.0000037841796938 en Y. Son unidades numéricas de las fuentes, sin certificación de metros ni de exactitud de campo.

Se volvió a abrir el archivo local con la geometría visible y se exportó de nuevo el terreno. Este cotejo conserva 114 548 puntos, con el mismo orden y multiconjunto a tres decimales, y pasa los controles básicos de **228 439 caras**. Es una cara más que en la exportación inicial; se conservan ambas evidencias sin afirmar igualdad de triangulación.

## Resultados y criterios de aceptación

| Control | Criterio | Resultado |
| --- | --- | --- |
| Conversión DXF → XYZ | Mismas cadenas, orden y multiplicidad. | Reproducción idéntica por SHA-256. |
| Puntos de la exportación local final | Mismo orden y multiconjunto a precisión exportada. | 114 548 / 114 548; cero faltantes o adicionales. |
| Tolerancia del CSV local | Error absoluto ≤0.0005 por eje. | Máximo 0.0000062866210937. |
| Índices de caras de la exportación local | Base demostrable e índices dentro de rango. | Base cero; 0–114 547. |
| Controles básicos de sus triángulos | Sin índices repetidos, caras repetidas ni área cero. | 228 439 caras; cero incidencias. |
| Cobertura de ubicaciones únicas del modelo local | Todos los XYZ únicos referenciados. | 114 259 / 114 259. |
| Exportación previa de taladros | Mismas seis coordenadas y sin filas adicionales. | 153 / 153 en la prueba Import Pattern. |
| Registros del archivo local final | Tamaños lógicos de las listas geométricas. | 114 548 puntos y 153 referencias; 153 geometrías distintas. |
| Capa final Floating Holes | Concordancia con el modelo Single de coordenadas locales. | 153 / 153 filas; cero discrepancias. |
| Persistencia del archivo nativo | Guardar y reabrir con geometría visible. | Comprobado. |

Los controles de triángulos son básicos y corresponden a la exportación indicada. No comprueban toda posible intersección, orientación, hueco, validez de contorno o exactitud del levantamiento. La tolerancia del CSV deriva de su redondeo, no de una especificación topográfica de campo. En el CSV local, los máximos por eje son X=0.0000045166015625, Y=0.0000062866210937 y Z=0.0000049438476562. La lectura de puntos Single del nativo final presenta otras diferencias: hasta 0.0000114440918018 por eje; se registra como una representación distinta y no se confunde con el cotejo CSV.

## Decisiones técnicas y aprendizajes

- **Separar procedencias:** compartir carpeta no implica compartir ubicación o referencia espacial.
- **Preservar repeticiones:** registrar duplicados explica la diferencia entre puntos almacenados y vértices utilizados.
- **Distinguir exactitud y redondeo:** coincidir a cierta precisión no equivale a conservar cadenas decimales idénticas.
- **Verificar el relieve tras importar:** la vista por sí sola no sustituye el cotejo de la superficie.
- **Separar evidencias por etapa:** una exportación validada anteriormente no acredita un estado posterior del documento.
- **Proteger entradas:** las utilidades rechazan una salida que coincida con un origen; el conversor también rechaza archivos existentes.
- **Comprobar la representación guardada:** un recuento correcto y una imagen plausible no aseguran conservación decimal; la referencia local y su origen deben quedar explícitos.

## Alcance pendiente para otra etapa

Antes de tratar los datos como un levantamiento certificado, hacen falta la definición del CRS, datum, unidades, procedencia y controles de campo. El recuento de Floating Holes ya tiene evidencia estructural independiente; no se obtuvo por una exportación soportada de la capa. Las fuentes no aportan identificadores propios ni propiedades técnicas completas de los taladros.

El caso queda documentado como integración y comprobación de geometría. No acredita ejecución en campo, experiencia laboral en una operación minera ni validación de un plan de voladura.

## Evidencias

- [Resultados estructurados y hashes](resultados-fuentes.json).
- [Guía para repetir el proceso](uso-reproducible.md).
- [Comprobación detallada](verificacion-datos.md).
- [Diagnóstico de precisión y lectura estructural](precision-coordenadas.md).
- Dos capturas seleccionadas en la portada del repositorio.
