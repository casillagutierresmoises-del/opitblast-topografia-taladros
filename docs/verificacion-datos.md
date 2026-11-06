# Comprobación de los datos de entrada

Revisión realizada el **5 de noviembre de 2026**. Esta revisión corresponde a estructura y geometría de archivos, no a una evaluación de diseño de voladura.

## Nube topográfica

`Terrain K - Cloud 2.dxf` contiene entidades `POINT`, no caras trianguladas. El recuento de entidades en el texto del DXF coincide con la lectura de ezdxf:

| Control | Resultado |
| --- | ---: |
| Registros POINT | 114 548 |
| Coordenadas XYZ únicas | 114 259 |
| Repeticiones exactas | 289 |
| Capas con puntos | 1: `CLOUD_001` |

El archivo utiliza DXF R12/AC1009 y no declara `$INSUNITS` ni `$MEASUREMENT`. No se deducen un datum o unidades sólo por la magnitud de las coordenadas.

## Floating Holes

153 filas con seis campos de coordenadas. Valores numéricos completos y finitos, sin filas duplicadas.

| Columna del archivo | Campo geométrico |
| --- | --- |
| X | X de la boca |
| Y | Y de la boca |
| Z | Z de la boca |
| X_Toe | X del fondo |
| Y_Toe | Y del fondo |
| Z_Toe | Z del fondo |

Sus posiciones XY están dentro de la nube topográfica. No aporta identificadores propios ni diámetros. La diferencia entre boca y fondo define la longitud geométrica de sus segmentos; no se debe sustituir por una longitud elegida arbitrariamente.

## Malla Ejemplo

195 filas con 195 ID distintos. Campos `ID,ESTE,NORTE,ELEV` completos y sin duplicados de fila.

| Columna del archivo | Correspondencia |
| --- | --- |
| ID | Identificador original |
| ESTE | X |
| NORTE | Y |
| ELEV | Z |

Este conjunto está muy alejado de Terrain K y sus cotas son distintas. No se combina con la nube principal ni se desplaza para hacerlo coincidir. Tampoco se inventan longitud, fondo o diámetro ausentes.

## Preservación

Los archivos originales se leen sin modificarlos. Las copias preparadas registran sus hashes y conservan las cadenas decimales de las coordenadas originales. El software, las bibliotecas de su instalación, licencias, manuales del fabricante y datos originales quedan fuera del repositorio.

## Prueba previa: exportación desde Import Pattern

El **6 de noviembre de 2026**, durante una prueba con `Import Pattern`, se generó una exportación de **153 taladros** mediante `Boreholes → Export`, en formato CSV. El cotejo con `Floating Holes` confirmó:

| Control de la exportación | Resultado |
| --- | ---: |
| Filas de la fuente y de la exportación | 153 / 153 |
| Seis coordenadas iguales por orden de fila | Sí |
| Geometrías iguales sin depender del orden | Sí |
| Filas faltantes / adicionales | 0 / 0 |
| Geometrías o collares XY repetidos en la exportación | 0 |
| Longitud geométrica mínima / máxima | 13.774 / 14.305 |
| Longitudes fuera de la tolerancia de 0.000001 | 0 |

La comprobación numérica está registrada en [resultados-fuentes.json](resultados-fuentes.json). Acredita conservación de coordenadas en esa exportación previa, sin validar parámetros de diseño ni el recuento de la capa final de Floating Holes.

### Restauración y cotejo del relieve

La superficie plana generada desde los collares (Z=98) se sustituyó por la nube original. La comprobación de una exportación nativa del terreno dio estos resultados:

| Control del terreno exportado | Resultado |
| --- | ---: |
| Puntos de la fuente y de la exportación | 114 548 / 114 548 |
| Posiciones XYZ únicas | 114 259 |
| Registros coincidentes repetidos | 289 |
| Triángulos válidos | 228 438 |
| Coordenadas iguales por orden a tres decimales | Sí |
| Mismo multiconjunto de coordenadas a tres decimales | Sí |
| Error absoluto máximo | 0.0000037841796875 |
| Tolerancia del cotejo | 0.0005 |

Las coordenadas del terreno pasan el cotejo dentro de esa tolerancia; no se afirma identidad decimal exacta.

## Estado final: Floating Holes sobre el relieve

Tras restaurar el terreno, se usó `Boreholes → Floating Holes → Import` con el CSV original de 153 registros. Se mapearon las seis coordenadas de boca y fondo, usando coma como separador. La importación mostró progreso y la distribución quedó visible sobre el banco, manteniendo el relieve.

La comprobación de esta capa final es visual. No se atribuye a ella el cotejo de 153/153 de la prueba previa de Import Pattern. El recuento y la exportación nativa final de la capa Floating Holes no quedaron acreditados en esta etapa.

El proyecto `TerrainK_Topografia_FloatingHoles.opit` se guardó y volvió a abrir con el relieve y la distribución visibles. Las tres capturas del repositorio proceden de esa sesión. El archivo nativo y los CSV de trabajo se conservan localmente.
