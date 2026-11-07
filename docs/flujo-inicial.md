# Flujo inicial: topografía y coordenadas de taladros

## 1. Identificar la sesión

Comprobar el ejecutable y la versión **1.5.93.0**. En este PC, el nombre registrado de la aplicación puede confundirse con O-PitSurface; el nombre por sí solo no identifica la versión activa.

## 2. Preservar el punto de partida

Guardar una copia mediante `File → Save as` antes de incorporar o sustituir datos. El formato nativo de esta versión utiliza la extensión `.opit`.

## 3. Comprobar la topografía

Comparar su ubicación y escala con el conjunto que se quiere importar. Si se necesita incorporar la nube, usar `Topography → Import Terrain` y los formatos admitidos por el diálogo activo. `Import Layer` añade una capa y no acredita que se haya creado la topografía.

Para una conversión de DXF de puntos a CSV XYZ, preservar los ejes, las cotas, el orden de filas y la precisión del origen. La copia preparada en esta práctica conserva los 114 548 registros, incluidos los puntos coincidentes; el original permanece intacto.

## 4. Incorporar los datos de Floating Holes

Para el estado final de esta práctica, usar `Boreholes → Floating Holes → Import`. Abrir el CSV original, seleccionar la coma como separador y revisar la previsualización antes de confirmar.

Mapear `X`, `Y`, `Z` a las coordenadas de boca, y `X_Toe`, `Y_Toe`, `Z_Toe` a `X_TOE`, `Y_TOE`, `Z_TOE`. No intercambiar ejes ni modificar la cota de las bocas para ajustarlas automáticamente al terreno.

La capa de Floating Holes se observa sobre la topografía existente sin crear un terreno nuevo desde los collares.

### Prueba previa con Import Pattern

En una etapa anterior se ensayó `Boreholes → Import Pattern` y se comprobó su exportación numérica. Para ese flujo, una columna opcional `LENGTH` se puede obtener de la distancia boca–fondo, sin inventar un fondo diferente. El resultado de esa prueba no se usa como acreditación del recuento de la capa final de Floating Holes.

Un terreno creado desde los collares planos sustituye el relieve por una superficie distinta. Si un importador pregunta por crear ese terreno y ya existe una topografía verificada, conservar la topografía existente.

## 5. Verificar antes de dar la importación por terminada

- Contrastar el número de registros de la capa correspondiente con las 153 filas de origen cuando la aplicación exponga ese recuento.
- Revisar primeras y últimas coordenadas de boca y fondo.
- Comprobar que los taladros se sitúan sobre la zona esperada, sin intercambio X/Y ni desplazamiento de coordenadas.
- Mantener aparte `Malla Ejemplo`, pues corresponde a otro conjunto y no aporta longitud ni fondo.
- Guardar el proyecto final y comprobar que se puede volver a abrir.

La presencia de un archivo guardado o de un botón accesible no sustituye la comprobación de los datos importados.

## 6. Registrar evidencias

Capturar una vista de la topografía, una vista de la distribución de taladros y, si está disponible, el cuadro con el recuento. Mostrar el resultado real de la sesión. No incluir otras aplicaciones, conversaciones, cuentas ni rutas personales innecesarias.

## 7. Referencia local y precisión de la capa guardada

La revisión posterior del archivo detectó pérdida de precisión en las referencias importadas con coordenadas grandes. Se preparó una copia explícitamente local con el mismo origen para terreno, boca y fondo; se conservaron las fuentes globales. El proyecto final se guarda como `TerrainK_Geometria_Local.opit` y debe acompañarse de `TerrainK_Geometria_Local.origen.json`.

La [auditoría de precisión](precision-coordenadas.md) documenta el origen, la transformación inversa, el recuento de 153 referencias y el cotejo de la nueva exportación de 228 439 caras. Es una capa de referencia geométrica; no se convirtió en un patrón de diseño nuevo.
