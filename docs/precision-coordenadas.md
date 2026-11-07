# Precisión de coordenadas y referencia local

## Resultado comprobado

El archivo final `TerrainK_Geometria_Local.opit` contiene **114 548 registros de terreno y 153 referencias Floating Holes**, con 153 geometrías distintas de seis componentes. Este recuento se obtuvo mediante lectura estructural del archivo guardado y se distingue del posterior cotejo de puntos y caras exportados por O-PitBlast. La lectura estructural no es una API oficial del fabricante. El proyecto local también se volvió a abrir con la geometría visible.

La comprobación se centra en la geometría y la representación numérica. Las diferencias siguientes se expresan en **las unidades numéricas de las fuentes**; no se presentan como metros certificados o precisión de un levantamiento.

## Lectura estructural sin deserializar objetos de la aplicación

Se utilizó `System.Formats.Nrbf.NrbfDecoder` del runtime oficial de .NET 10 para leer registros y valores primitivos. Microsoft documenta este lector como una forma de decodificar NRBF sin ejecutar la deserialización de `BinaryFormatter` ni cargar los tipos indicados por el archivo. [Guía oficial de Microsoft](https://learn.microsoft.com/en-us/dotnet/standard/serialization/binaryformatter-migration-guide/read-nrbf-payloads).

En esta comprobación se limitó la lectura a las listas geométricas y sus componentes: tamaño lógico, coordenadas y tipo primitivo. Se distinguió el tamaño lógico de la capacidad reservada; una capacidad de 256 no equivale a 256 referencias. No se llamó a `BinaryFormatter.Deserialize`, no se cargaron DLL de O-PitBlast y no se instanciaron sus clases. El SHA-256 antes y después acredita que el archivo auditado no cambió durante la lectura.

Los componentes examinados están representados como `System.Single`, de precisión simple. Este tipo no conserva cualquier cadena decimal exactamente; su precisión finita exige distinguir una coordenada de origen de su representación binaria. [Referencia de Microsoft sobre Single](https://learn.microsoft.com/en-us/dotnet/api/system.single?view=net-10.0).

## Hallazgo en la primera importación

La lectura del primer proyecto, `TerrainK_Topografia_FloatingHoles.opit`, ya encontró 153 referencias y 153 geometrías distintas. Sin embargo, reconstruir sus coordenadas globales reveló diferencias mayores en X e Y que las aparentes en la vista del programa.

| Máxima diferencia absoluta reconstruida | Primera importación | Archivo final en referencia local |
| --- | ---: | ---: |
| X de boca y fondo | 0.050500732421875 | 0.000003723144535 |
| Y de boca y fondo | 0.4419974975585938 | 0.0000037841796938 |
| Z de boca | 3e-16 | 3e-16 |
| Z de fondo | 0.00000378417968745 | 0.0000000145435333 |

La comparación distingue dos modelos numéricos: convertir las coordenadas globales a precisión simple antes de restar un origen, o restar el origen antes de esa conversión. El primer modelo reproduce las 153 filas de la importación inicial; el segundo reproduce las 153 filas del archivo final, sin discrepancias de fila en cada comparación correspondiente.

**La secuencia de conversiones es una inferencia numérica ensayada contra los registros**, no una auditoría del código fuente del fabricante. Tampoco convierte este lector en una interfaz soportada por O-PitBlast.

## Traslación reversible documentada

Se prepararon copias de trabajo restando el **mismo origen**, calculado exclusivamente como el mínimo XYZ del terreno, a todos los puntos del terreno y a ambas extremidades de Floating Holes:

| Eje | Origen decimal |
| --- | ---: |
| X | 530180.832000732421875 |
| Y | 7821922.6989974975585938 |
| Z | 83.7659988403320313 |

```text
coordenada_local = coordenada_global − origen
coordenada_global = coordenada_local + origen
```

La preparación utilizó `Decimal` con precisión 60 y rechazo de operaciones inexactas. Se verificaron la inversión decimal de todas las filas, el orden, las repeticiones y las diferencias vectoriales. Aplicar una misma traslación a ambos extremos conserva algebraicamente las distancias. No se cambiaron ejes, escala, unidades ni CRS. Los originales globales permanecieron intactos y sus hashes se conservaron.

La exactitud de esa preparación decimal no implica exactitud decimal del posterior almacenamiento en `Single`. El cotejo final mide precisamente esa diferencia de representación.

## Terreno: representación Single y exportación CSV

La representación de puntos `Single` leída del archivo final tiene estas máximas diferencias globales reconstruidas respecto de la nube de origen:

| Eje | Diferencia máxima |
| --- | ---: |
| X | 0.0000076293945375 |
| Y | 0.0000114440918018 |
| Z | 0.0000050067901612 |

Esta lectura no es el CSV exportado por la aplicación. En el archivo local se realizó una nueva exportación de puntos y caras y se cotejó con `TerrainK_local_XYZ.csv`. El resultado conserva 114 548 registros, 114 259 XYZ únicos y 289 repeticiones; mantiene el orden y el multiconjunto de coordenadas a los tres decimales exportados.

| Error absoluto máximo del cotejo CSV local | Valor |
| --- | ---: |
| X | 0.0000045166015625 |
| Y | 0.0000062866210937 |
| Z | 0.0000049438476562 |

Los tres errores son inferiores a 0.0005. Las **228 439 caras** de esta exportación tienen índices base cero dentro de rango, sin índices repetidos por cara, caras duplicadas ni área cero. Las caras representan las 114 259 ubicaciones XYZ únicas; sólo quedan sin referencia 289 registros redundantes.

La exportación previa en coordenadas globales tenía **228 438 caras** y un máximo de 0.0000037841796875 en su propio cotejo CSV. El modelo local final tiene una cara más: no se afirma identidad de triangulación entre etapas. Los controles básicos no acreditan toda posible intersección, orientación o validez de contorno, y el recuento estructural por sí solo tampoco los sustituye.

## Trazabilidad y límites

Archivo final auditado: `TerrainK_Geometria_Local.opit`.

```text
SHA-256: e4af2f524faa0b41a7e2bc8f5ee5409de4ae1c63b21e8d90471fa428363fbff6
```

El origen decimal explícito permite interpretar la referencia local; no se deduce un CRS de sus magnitudes ni se considera que un campo interno sin documentar certifique ese origen. El resultado acredita recuentos y concordancia numérica bajo los modelos expuestos. No certifica datos de campo, una transformación geodésica ni un plan operativo.
