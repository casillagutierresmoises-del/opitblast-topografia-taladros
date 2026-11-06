#!/usr/bin/env python3
"""Revisa tres CSV de geometría sin modificarlos ni transformarlos.

Uso (Python 3.10 o posterior, sólo biblioteca estándar):
    python scripts/verificar_geometria.py terreno.csv taladros.csv malla.csv
    python scripts/verificar_geometria.py terreno.csv taladros.csv malla.csv \
        --salida resultados.json
    python scripts/verificar_geometria.py terreno.csv taladros.csv malla.csv \
        --exportacion taladros_exportados.csv --salida resultados.json
    python scripts/verificar_geometria.py terreno.csv taladros.csv malla.csv \
        --terreno-exportado terreno_exportado.csv \
        --indices-exportados terreno_exportado_index.csv --salida resultados.json

Se esperan coma como separador, punto decimal y encabezados. El terreno usa
X,Y,Z; los taladros, X,Y,Z,X_Toe,Y_Toe,Z_Toe; la malla puede usar ID,ESTE,NORTE,ELEV
o X,Y,Z,ID. Los encabezados admiten espacios exteriores y mayúsculas/minúsculas.
El informe identifica archivos por nombre base y SHA-256, nunca por ruta.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import io
import json
from pathlib import Path
import sys


@dataclass
class Dataset:
    report: dict
    points: list[tuple[Decimal, Decimal, Decimal]]
    minimum: tuple[Decimal, Decimal, Decimal] | None
    maximum: tuple[Decimal, Decimal, Decimal] | None


def bounds(points):
    if not points:
        return None, None
    return (
        tuple(min(point[index] for point in points) for index in range(3)),
        tuple(max(point[index] for point in points) for index in range(3)),
    )


def bounds_report(minimum, maximum):
    if minimum is None:
        return None
    return {
        "min": {axis: str(value) for axis, value in zip("XYZ", minimum)},
        "max": {axis: str(value) for axis, value in zip("XYZ", maximum)},
    }


def inspect_csv(path: Path, role: str) -> Dataset:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError(f"No se pudo leer {path.name}: {error.strerror}") from None
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError(f"{path.name}: se requiere texto UTF-8.") from None

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",")
    try:
        headers = [value.strip() for value in next(reader)]
    except StopIteration:
        raise ValueError(f"{path.name}: archivo vacío.") from None
    normalized = [value.upper() for value in headers]
    if len(set(normalized)) != len(normalized) or any(not h for h in headers):
        raise ValueError(f"{path.name}: encabezados vacíos o repetidos.")

    aliases = {"X": ("X",), "Y": ("Y",), "Z": ("Z",)}
    if role == "malla":
        aliases = {"X": ("X", "ESTE"), "Y": ("Y", "NORTE"), "Z": ("Z", "ELEV")}
    if role == "taladros":
        aliases.update({"X_TOE": ("X_TOE",), "Y_TOE": ("Y_TOE",), "Z_TOE": ("Z_TOE",)})

    mapping = {}
    for target, candidates in aliases.items():
        matches = [index for index, header in enumerate(normalized) if header in candidates]
        if len(matches) != 1:
            raise ValueError(f"{path.name}: falta una columna inequívoca para {target}.")
        mapping[target] = matches[0]
    id_index = normalized.index("ID") if "ID" in normalized else None

    total_rows = 0
    invalid_rows = 0
    missing_coordinates = 0
    nonnumeric_coordinates = 0
    nonfinite_coordinates = 0
    examples = []
    points = []
    toes = []
    complete_geometry = set()
    repeated_geometry = 0
    identifiers = []
    blank_identifiers = 0
    lengths = []

    for row in reader:
        if not row or not any(value.strip() for value in row):
            continue
        total_rows += 1
        if len(row) != len(headers):
            invalid_rows += 1
            if len(examples) < 5:
                examples.append({"linea": reader.line_num, "problema": "número de columnas distinto del encabezado"})
            continue
        if id_index is not None:
            identifier = row[id_index]
            if identifier.strip():
                identifiers.append(identifier)
            else:
                blank_identifiers += 1

        parsed = {}
        problems = []
        for target, index in mapping.items():
            value = row[index].strip()
            if not value:
                missing_coordinates += 1
                problems.append(f"{headers[index]} vacío")
                continue
            try:
                number = Decimal(value)
            except InvalidOperation:
                nonnumeric_coordinates += 1
                problems.append(f"{headers[index]} no numérico")
                continue
            if not number.is_finite():
                nonfinite_coordinates += 1
                problems.append(f"{headers[index]} no finito")
                continue
            parsed[target] = number
        if problems:
            invalid_rows += 1
            if len(examples) < 5:
                examples.append({"linea": reader.line_num, "problemas": problems})
            continue

        point = tuple(parsed[axis] for axis in ("X", "Y", "Z"))
        points.append(point)
        geometry = point
        if role == "taladros":
            toe = tuple(parsed[axis] for axis in ("X_TOE", "Y_TOE", "Z_TOE"))
            toes.append(toe)
            geometry += toe
            with localcontext() as context:
                context.prec = 40
                lengths.append(sum((b - a) ** 2 for a, b in zip(point, toe)).sqrt())
        if geometry in complete_geometry:
            repeated_geometry += 1
        complete_geometry.add(geometry)

    minimum, maximum = bounds(points)
    report = {
        "rol": role,
        "archivo": path.name,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "filas": total_rows,
        "filas_geometricas_validas": len(points),
        "filas_invalidas": invalid_rows,
        "columnas": headers,
        "mapeo": {target: headers[index] for target, index in mapping.items()},
        "coordenadas_vacias": missing_coordinates,
        "coordenadas_no_numericas": nonnumeric_coordinates,
        "coordenadas_no_finitas": nonfinite_coordinates,
        "xyz_unicos": len(set(points)),
        "xyz_repetidos": len(points) - len(set(points)),
        "geometrias_completas_repetidas": repeated_geometry,
        "limites_xyz": bounds_report(minimum, maximum),
    }
    if examples:
        report["ejemplos_invalidos"] = examples
    if id_index is not None:
        report["identificadores"] = {
            "unicos": len(set(identifiers)),
            "repetidos": len(identifiers) - len(set(identifiers)),
            "vacios": blank_identifiers,
        }
    if role == "taladros":
        toe_minimum, toe_maximum = bounds(toes)
        report["limites_toe_xyz"] = bounds_report(toe_minimum, toe_maximum)
        report["distancia_collar_toe"] = {
            "cantidad": len(lengths),
            "min": str(min(lengths)) if lengths else None,
            "max": str(max(lengths)) if lengths else None,
            "distancias_cero": sum(value == 0 for value in lengths),
            "unidad": "misma unidad numérica de las coordenadas; no se aplica conversión",
        }
    return Dataset(report, points, minimum, maximum)


def compare_xy(first: Dataset, second: Dataset) -> dict:
    """Compara cajas XY, no triangulaciones ni pertenencia a una superficie."""
    overlap = None
    contained = None
    if first.minimum is not None and second.minimum is not None:
        overlap = all(
            first.minimum[index] <= second.maximum[index]
            and second.minimum[index] <= first.maximum[index]
            for index in (0, 1)
        )
        contained = sum(
            all(first.minimum[index] <= point[index] <= first.maximum[index] for index in (0, 1))
            for point in second.points
        )
    return {
        "a": first.report["rol"],
        "b": second.report["rol"],
        "solape_cajas_xy": overlap,
        "puntos_b_en_caja_xy_a": contained,
    }


def verify_native_export(source_path: Path, export_path: Path) -> dict:
    """Coteja sólo coordenadas y longitud; omite otros atributos de la exportación."""
    coordinate_names = ("X", "Y", "Z", "X_TOE", "Y_TOE", "Z_TOE")

    def read_coordinates(path, require_length):
        try:
            payload = path.read_bytes()
            reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")), skipinitialspace=True)
            if reader.fieldnames is None:
                raise ValueError("no hay encabezado")
            reader.fieldnames = [header.strip().upper() for header in reader.fieldnames]
            required = coordinate_names + (("LENGTH",) if require_length else ())
            if len(set(reader.fieldnames)) != len(reader.fieldnames) or any(name not in reader.fieldnames for name in required):
                raise ValueError("faltan columnas inequívocas de coordenadas o LENGTH")
            coordinates, lengths = [], []
            for row in reader:
                if None in row or any(row.get(name) is None for name in required):
                    raise ValueError(f"fila de ancho incorrecto en línea {reader.line_num}")
                values = tuple(Decimal(row[name].strip()) for name in required)
                if not all(value.is_finite() for value in values):
                    raise ValueError(f"valor no finito en línea {reader.line_num}")
                coordinates.append(values[:6])
                if require_length:
                    lengths.append(values[6])
            return payload, coordinates, lengths
        except (OSError, UnicodeDecodeError, InvalidOperation, ValueError) as error:
            # No se publican valores de filas ni rutas del equipo.
            detail = error.strerror if isinstance(error, OSError) else str(error)
            raise ValueError(f"{path.name}: no se pudo cotejar la exportación ({detail}).") from None

    source_bytes, source, _ = read_coordinates(source_path, False)
    export_bytes, exported, reported_lengths = read_coordinates(export_path, True)
    computed_lengths = []
    for row in exported:
        with localcontext() as context:
            context.prec = 40
            computed_lengths.append(sum((row[index + 3] - row[index]) ** 2 for index in range(3)).sqrt())
    errors = [abs(reported - computed) for reported, computed in zip(reported_lengths, computed_lengths)]
    tolerance = Decimal("0.000001")
    missing = sum((Counter(source) - Counter(exported)).values())
    additional = sum((Counter(exported) - Counter(source)).values())
    duplicate_geometry = len(exported) - len(set(exported))
    length_mismatches = sum(error > tolerance for error in errors)
    return {
        "metodo": "cotejo del CSV fuente con un CSV exportado desde la aplicación",
        "limite": "el script no identifica por sí solo la aplicación que generó el CSV ni valida parámetros de diseño",
        "fuente": source_path.name,
        "sha256_fuente": hashlib.sha256(source_bytes).hexdigest(),
        "exportacion": export_path.name,
        "sha256_exportacion": hashlib.sha256(export_bytes).hexdigest(),
        "filas_fuente": len(source),
        "filas_exportadas": len(exported),
        "seis_coordenadas_iguales_por_orden": source == exported,
        "geometrias_iguales_sin_orden": Counter(source) == Counter(exported),
        "collares_xy_iguales_sin_orden": Counter(row[:2] for row in source) == Counter(row[:2] for row in exported),
        "geometrias_exportadas_repetidas": duplicate_geometry,
        "collares_xy_exportados_repetidos": len(exported) - len({row[:2] for row in exported}),
        "filas_faltantes": missing,
        "filas_adicionales": additional,
        "distancia_min": str(min(computed_lengths)) if computed_lengths else None,
        "distancia_max": str(max(computed_lengths)) if computed_lengths else None,
        "tolerancia_longitud": str(tolerance),
        "longitudes_fuera_tolerancia": length_mismatches,
        "max_error_longitud": str(max(errors)) if errors else None,
        "coincidencia_completa": source == exported and missing == additional == length_mismatches == 0,
    }


def verify_topography_export(source: Dataset, points_path: Path, indices_path: Path) -> dict:
    """Contrasta la nube a la precisión exportada y comprueba índices de caras."""
    exported = inspect_csv(points_path, "terreno_exportado")
    if exported.report["filas_invalidas"] or not exported.points:
        raise ValueError(f"{points_path.name}: la exportación contiene coordenadas inválidas o está vacía.")
    precisions = Counter(-value.as_tuple().exponent for point in exported.points for value in point)
    if len(precisions) != 1:
        raise ValueError(f"{points_path.name}: la precisión no es uniforme; no se asignará una tolerancia automáticamente.")
    decimals = next(iter(precisions))
    quantum = Decimal(1).scaleb(-decimals)
    tolerance = quantum / 2
    rounded_source = [tuple(value.quantize(quantum, rounding=ROUND_HALF_EVEN) for value in point) for point in source.points]
    same_order = rounded_source == exported.points
    maximum_errors = [max(abs(a[index] - b[index]) for a, b in zip(source.points, exported.points)) for index in range(3)] if same_order else None

    try:
        payload = indices_path.read_bytes()
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")), skipinitialspace=True)
        if reader.fieldnames is None:
            raise ValueError("no hay encabezado")
        reader.fieldnames = [header.strip().upper() for header in reader.fieldnames]
        if any(name not in reader.fieldnames for name in ("T1", "T2", "T3")):
            raise ValueError("se requieren T1,T2,T3")
        faces = [tuple(int(row[name].strip()) for name in ("T1", "T2", "T3")) for row in reader]
        if not faces:
            raise ValueError("no hay caras")
    except (OSError, UnicodeDecodeError, ValueError, AttributeError, KeyError) as error:
        detail = error.strerror if isinstance(error, OSError) else str(error)
        raise ValueError(f"{indices_path.name}: índices no válidos ({detail}).") from None

    vertex_count = len(exported.points)
    indices = [index for face in faces for index in face]
    valid_zero = all(0 <= index < vertex_count for index in indices)
    valid_one = all(1 <= index <= vertex_count for index in indices)
    base = 0 if valid_zero and not valid_one else 1 if valid_one and not valid_zero else None
    used = set(indices)
    zero_area = None
    represented_sites = None
    if base is not None:
        represented_sites = {exported.points[index - base] for index in used}
        zero_area = 0
        for face in faces:
            a, b, c = [exported.points[index - base] for index in face]
            u = [b[index] - a[index] for index in range(3)]
            v = [c[index] - a[index] for index in range(3)]
            cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
            zero_area += all(value == 0 for value in cross)
    canonical_faces = {tuple(sorted(face)) for face in faces}
    same_multiset = Counter(rounded_source) == Counter(exported.points)
    return {
        "alcance": "coincidencia de puntos a la precisión del CSV exportado; no igualdad decimal exacta ni validación integral de la superficie",
        "fuente": source.report["archivo"], "sha256_fuente": source.report["sha256"],
        "exportacion_puntos": points_path.name, "sha256_exportacion_puntos": exported.report["sha256"],
        "exportacion_indices": indices_path.name, "sha256_exportacion_indices": hashlib.sha256(payload).hexdigest(),
        "puntos_fuente": len(source.points), "xyz_unicos_fuente": len(set(source.points)),
        "puntos_repetidos_fuente": len(source.points)-len(set(source.points)),
        "puntos_exportados": vertex_count, "xyz_unicos_exportados": len(set(exported.points)),
        "puntos_repetidos_exportados": vertex_count-len(set(exported.points)),
        "decimales_exportados": decimals, "paso_redondeo": str(quantum), "tolerancia_por_coordenada": str(tolerance),
        "mismo_multiconjunto_redondeado": same_multiset,
        "mismo_conjunto_redondeado": set(rounded_source) == set(exported.points),
        "mismo_orden_redondeado": same_order,
        "puntos_faltantes_con_multiplicidad": sum((Counter(rounded_source)-Counter(exported.points)).values()),
        "puntos_adicionales_con_multiplicidad": sum((Counter(exported.points)-Counter(rounded_source)).values()),
        "max_error_orden_xyz": [str(error) for error in maximum_errors] if maximum_errors else None,
        "max_error_limites_xyz": [str(max(abs(source.minimum[index]-exported.minimum[index]),abs(source.maximum[index]-exported.maximum[index]))) for index in range(3)],
        "caras": len(faces), "indice_min": min(indices), "indice_max": max(indices),
        "base_indices_demostrada": base, "indices_validos_base_cero": valid_zero, "indices_validos_base_uno": valid_one,
        "caras_con_indices_repetidos": sum(len(set(face))<3 for face in faces),
        "caras_repetidas_sin_orientacion": len(faces)-len(canonical_faces),
        "caras_area_cero_segun_puntos_exportados": zero_area,
        "vertices_referenciados": len(used), "vertices_no_referenciados": vertex_count-len(used),
        "sitios_xyz_representados_por_caras": len(represented_sites) if represented_sites is not None else None,
        "sitios_xyz_sin_caras": len(set(exported.points)-represented_sites) if represented_sites is not None else None,
        "coincidencia_a_precision_exportada": same_multiset and same_order and base is not None and all(error <= tolerance for error in maximum_errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("terreno", type=Path, help="CSV XYZ del terreno")
    parser.add_argument("taladros", type=Path, help="CSV con coordenadas de collar y toe")
    parser.add_argument("malla", type=Path, help="CSV de puntos de malla, con ID opcional")
    parser.add_argument("--exportacion", type=Path, help="CSV de taladros exportado desde O-PitBlast para cotejar seis coordenadas y LENGTH")
    parser.add_argument("--terreno-exportado", type=Path, help="CSV XYZ exportado desde O-PitBlast para cotejar la nube")
    parser.add_argument("--indices-exportados", type=Path, help="CSV T1,T2,T3 de la misma exportación del terreno")
    parser.add_argument("--salida", type=Path, help="Archivo JSON opcional; por defecto se imprime")
    arguments = parser.parse_args()
    if bool(arguments.terreno_exportado) != bool(arguments.indices_exportados):
        parser.error("--terreno-exportado y --indices-exportados deben proporcionarse juntos")
    try:
        terrain = inspect_csv(arguments.terreno, "terreno")
        holes = inspect_csv(arguments.taladros, "taladros")
        pattern = inspect_csv(arguments.malla, "malla")
        datasets = [terrain, holes, pattern]
        comparisons = [compare_xy(terrain, holes), compare_xy(terrain, pattern), compare_xy(holes, pattern)]
        warnings = []
        for comparison in comparisons:
            if comparison["solape_cajas_xy"] is False:
                warnings.append(
                    f"{comparison['a']} y {comparison['b']} tienen cajas XY disjuntas: "
                    "revisar su procedencia y sistema de referencia antes de combinarlos. No se han transformado."
                )
        if any(dataset.report["filas_invalidas"] for dataset in datasets):
            warnings.append("Hay filas inválidas; sus coordenadas se excluyen de límites y distancias.")
        result = {
            "version_esquema": 1,
            "alcance": "inspección de CSV; no demuestra su importación en O-PitBlast",
            "convenciones": {
                "separador": ",", "decimal": ".", "codificacion": "UTF-8",
                "limites_y_distancias": "cadenas decimales para conservar precisión",
                "crs_y_unidades": "no se deducen de las magnitudes de las coordenadas",
                "duplicados": "igualdad numérica de XYZ o de los seis componentes collar/toe",
                "solape": "sólo cajas envolventes XY; no acredita coincidencia de terrenos",
            },
            "fuentes": [dataset.report for dataset in datasets],
            "comparaciones": comparisons,
            "advertencias": warnings,
        }
        native_valid = True
        if arguments.exportacion:
            result["verificacion_exportacion_nativa"] = verify_native_export(arguments.taladros, arguments.exportacion)
            native_valid = result["verificacion_exportacion_nativa"]["coincidencia_completa"]
        if arguments.terreno_exportado:
            result["verificacion_topografia_nativa"] = verify_topography_export(terrain, arguments.terreno_exportado, arguments.indices_exportados)
            native_valid = native_valid and result["verificacion_topografia_nativa"]["coincidencia_a_precision_exportada"]
        output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if arguments.salida:
            arguments.salida.parent.mkdir(parents=True, exist_ok=True)
            arguments.salida.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 2 if any(dataset.report["filas_invalidas"] for dataset in datasets) or not native_valid else 0
    except (ValueError, csv.Error) as error:
        print(f"Error de datos: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
