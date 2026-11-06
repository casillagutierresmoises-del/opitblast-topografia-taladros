# Reproducir el control geométrico

## Requisitos

Python **3.10 o posterior**, con biblioteca estándar. Los dos scripts no requieren pip ni conexión al programa. O-PitBlast 1.5.93.0 se utilizó para importaciones, exportaciones nativas y evidencia de interfaz.

Ejecutar los comandos desde la raíz del repositorio. Ajustar las rutas entre comillas a una copia propia de los archivos. Los originales del taller y el proyecto nativo no se distribuyen.

## 1. Repetir la extracción del DXF

```sh
python scripts/convertir_nube_dxf.py "datos/Terrain K - Cloud 2.dxf" "trabajo/TerrainK_XYZ.csv" --capa CLOUD_001 --puntos-esperados 114548 --sha256-esperado 3a99f1abbef5450e7fa6d0a78dd0ddf6ffa39859e999e42f650ab09d4c041d70
```

Crear antes la carpeta `trabajo`. La salida debe ser un archivo nuevo. El conversor conserva cadenas numéricas, orden y duplicados, y sólo extrae POINT con XYZ explícitos de ENTITIES de un DXF ASCII. No resuelve inserciones, bloques, otras entidades, transformaciones o un sistema de referencia.

El informe JSON se imprime por la salida estándar. Para la fuente del taller, el CSV debe tener 114 548 registros y SHA-256 `9023dd94103cc00f8d1297981cdfcea3e7f04a358b6a1ce77692a4e971b39e23`.

## 2. Inspeccionar las tres fuentes

```sh
python scripts/verificar_geometria.py "trabajo/TerrainK_XYZ.csv" "datos/Floating Holes.csv" "datos/Malla Ejemplo.csv" --salida "trabajo/inspeccion.json"
```

Se esperan coma, punto decimal y encabezados UTF-8. Se aceptan espacios exteriores y diferencias de mayúsculas en encabezados.

| Archivo | Campos |
| --- | --- |
| Terreno | X,Y,Z |
| Coordenadas de taladros | X,Y,Z,X_Toe,Y_Toe,Z_Toe |
| Malla separada | ID,ESTE,NORTE,ELEV o X,Y,Z,ID |

El informe incluye hashes, filas válidas e inválidas, coordenadas no finitas, repetidos, límites y solape de cajas XY. Un solape no demuestra un CRS común ni coincidencia de superficies.

## 3. Cotejar exportaciones nativas

Después de generar desde el programa los CSV de puntos y caras del mismo terreno:

```sh
python scripts/verificar_geometria.py "trabajo/TerrainK_XYZ.csv" "datos/Floating Holes.csv" "datos/Malla Ejemplo.csv" --terreno-exportado "trabajo/terreno_exportado.csv" --indices-exportados "trabajo/terreno_exportado_index.csv" --salida "trabajo/cotejo-terreno.json"
```

Los índices requieren T1,T2,T3 y una base cero o uno demostrable. El programa separa la coincidencia de puntos de los controles básicos de triangulación. El caso real pasa ambos; 289 registros redundantes sin referencia no dejan ubicaciones únicas fuera de las caras.

Para repetir **la prueba previa de Import Pattern**, añadir:

```text
--exportacion "trabajo/taladros_exportados.csv"
```

Ese CSV requiere las seis coordenadas y `Length`. El script verifica el archivo entregado: no identifica por sí solo su origen, no abre `.opit` ni acredita el estado final de Floating Holes.

## 4. Leer el resultado

| Código | Significado |
| --- | --- |
| 0 | El comando terminó y pasaron los controles solicitados. |
| 2 | Error de datos o controles fallidos; revisar el informe o stderr. |

La incompatibilidad de cajas XY se informa como advertencia: dos conjuntos pueden ser válidos por separado. No se corrigen ni combinan automáticamente.

`--salida` no puede apuntar a ninguna entrada, incluidas exportaciones opcionales. Elegir un nombre nuevo para conservar informes anteriores. El conversor exige además que su CSV no exista.

## 5. Ejecutar las pruebas

```sh
python -m unittest discover -s tests -v
```

Las pruebas usan archivos temporales y datos sintéticos. Comprueban preservación de entradas, extracción de coordenadas y rechazo de geometría o conectividad inválidas. No incluyen ni necesitan los originales del taller.

La comprobación de los 114 548 puntos reales se ejecutó localmente además de estas pruebas. Los resultados agregados están en [resultados-fuentes.json](resultados-fuentes.json).

## Referencias de CI

El flujo de GitHub Actions ejecuta las mismas pruebas en Linux y Windows con permisos de lectura. Utiliza las acciones oficiales [checkout](https://github.com/actions/checkout) y [setup-python](https://github.com/actions/setup-python).
