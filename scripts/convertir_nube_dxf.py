#!/usr/bin/env python3
"""Extrae POINT de un DXF ASCII a CSV X,Y,Z sin transformar coordenadas.

Python 3.10+, sólo biblioteca estándar. Conserva las cadenas decimales, el
orden y las repeticiones de los POINT de la sección ENTITIES. No evalúa
bloques, referencias, curvas, mallas ni sistemas de coordenadas CAD.

Uso:
    python scripts/convertir_nube_dxf.py nube.dxf nube_xyz.csv
    python scripts/convertir_nube_dxf.py nube.dxf nube_xyz.csv --capa PUNTOS
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sys


def parse_ascii_points(payload: bytes, layer: str | None = None):
    """Lee únicamente POINT explícitos, validando pares y secciones básicas."""
    if payload.startswith(b"AutoCAD Binary DXF") or b"\0" in payload:
        raise ValueError("Se requiere DXF ASCII; no se admiten archivos binarios.")
    try:
        lines = payload.decode("ascii").splitlines()
    except UnicodeDecodeError:
        raise ValueError("Se requiere un DXF de texto ASCII.") from None
    if not lines or len(lines) % 2:
        raise ValueError("El DXF contiene un par código/valor incompleto o está vacío.")
    rows, included_layers = [], Counter()
    detected_layers, ignored_entities = Counter(), Counter()
    section, pending_section, eof_seen = None, False, False
    entities_seen = False
    entity_type, tags = None, {}

    def flush_entity():
        if section != "ENTITIES" or entity_type is None:
            return
        if entity_type != "POINT":
            ignored_entities[entity_type] += 1
            return
        if not all(code in tags for code in (10, 20, 30)):
            raise ValueError("Un POINT no contiene las tres coordenadas explícitas 10,20,30.")
        xyz = tuple(tags[code] for code in (10, 20, 30))
        try:
            valid = all(Decimal(value).is_finite() for value in xyz)
        except InvalidOperation:
            valid = False
        if not valid:
            raise ValueError("Un POINT contiene coordenadas vacías, no numéricas o no finitas.")
        point_layer = tags.get(8, "0")
        detected_layers[point_layer] += 1
        if layer is None or point_layer == layer:
            rows.append(xyz)
            included_layers[point_layer] += 1

    for line_index in range(0, len(lines), 2):
        try:
            code = int(lines[line_index].strip())
        except ValueError:
            raise ValueError(f"Código de grupo no válido en la línea {line_index + 1}.") from None
        if code < 0:
            raise ValueError(f"Código de grupo negativo en la línea {line_index + 1}.")
        value = lines[line_index + 1].strip()
        if eof_seen:
            raise ValueError("Hay datos después del marcador EOF.")
        if pending_section:
            if code != 2 or not value:
                raise ValueError("Una SECTION no tiene un nombre explícito de grupo 2.")
            section, pending_section = value, False
            if section == "ENTITIES":
                if entities_seen:
                    raise ValueError("El DXF contiene varias secciones ENTITIES.")
                entities_seen = True
            continue
        if code == 0:
            flush_entity()
            entity_type, tags = None, {}
            if value == "SECTION":
                if section is not None:
                    raise ValueError("Se encontró una SECTION anidada sin ENDSEC.")
                pending_section = True
            elif value == "ENDSEC":
                if section is None:
                    raise ValueError("Se encontró ENDSEC fuera de una sección.")
                section = None
            elif value == "EOF":
                if section is not None:
                    raise ValueError("Falta ENDSEC antes del marcador EOF.")
                eof_seen = True
            elif section is None:
                raise ValueError("Se encontró una entidad fuera de una sección.")
            elif section == "ENTITIES":
                if not value:
                    raise ValueError("Una entidad no tiene un tipo explícito.")
                entity_type = value
            continue
        if section is None:
            if code != 999:
                raise ValueError("Hay datos fuera de una sección.")
        elif section == "ENTITIES":
            if entity_type is None:
                raise ValueError("Hay atributos sin una entidad en ENTITIES.")
            if entity_type == "POINT" and code in (8, 10, 20, 30):
                if code in tags:
                    raise ValueError("Un POINT contiene campos de capa o coordenadas repetidos.")
                tags[code] = value
    if pending_section or section is not None or not eof_seen:
        raise ValueError("El DXF no termina con las secciones cerradas y un marcador EOF.")
    if not entities_seen or not detected_layers:
        raise ValueError("No se encontraron entidades POINT explícitas en ENTITIES.")
    if not rows:
        raise ValueError("No se encontraron POINT en la capa solicitada.")
    return rows, detected_layers, included_layers, ignored_entities


def convert(source: Path, destination: Path, *, layer: str | None = None,
            expected_sha256: str | None = None, expected_points: int | None = None) -> dict:
    if source.resolve() == destination.resolve():
        raise ValueError("La salida debe ser distinta del archivo de entrada.")
    if destination.exists():
        raise ValueError("La salida ya existe; elija un archivo nuevo.")
    if layer is not None and not layer:
        raise ValueError("La capa solicitada no puede estar vacía.")
    if expected_points is not None and expected_points < 1:
        raise ValueError("--puntos-esperados debe ser un entero positivo.")
    if expected_sha256 is not None:
        expected_sha256 = expected_sha256.lower()
        if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
            raise ValueError("--sha256-esperado debe contener 64 caracteres hexadecimales.")
    payload = source.read_bytes()
    source_hash = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and source_hash != expected_sha256:
        raise ValueError("El SHA-256 de la fuente no coincide con el esperado.")
    rows, detected_layers, included_layers, ignored_entities = parse_ascii_points(payload, layer)
    if expected_points is not None and len(rows) != expected_points:
        raise ValueError("El número de POINT incluidos no coincide con el esperado.")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(("X", "Y", "Z"))
    writer.writerows(rows)
    output = buffer.getvalue().encode("utf-8")
    roundtrip = list(csv.reader(io.StringIO(output.decode("utf-8"))))
    if roundtrip[0] != ["X", "Y", "Z"] or [tuple(row) for row in roundtrip[1:]] != rows:
        raise ValueError("La comprobación de ida y vuelta del CSV no conservó las coordenadas.")
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise ValueError("El archivo de origen cambió durante la conversión.")
    numeric_rows = [tuple(Decimal(value) for value in row) for row in rows]
    report = {
        "fuente": source.name, "sha256_fuente": source_hash,
        "salida": destination.name, "sha256_salida": hashlib.sha256(output).hexdigest(),
        "bytes_salida": len(output), "columnas": ["X", "Y", "Z"],
        "separador": ",", "decimal": ".", "codificacion": "UTF-8", "fin_de_linea": "LF",
        "puntos_detectados": sum(detected_layers.values()), "puntos_exportados": len(rows),
        "xyz_unicos": len(set(numeric_rows)), "xyz_repetidos": len(rows) - len(set(numeric_rows)),
        "capas_detectadas": dict(sorted(detected_layers.items())),
        "capas_incluidas": dict(sorted(included_layers.items())),
        "otras_entidades_omitidas": dict(sorted(ignored_entities.items())),
        "limites_xyz": {
            axis: {"min": str(min(row[index] for row in numeric_rows)),
                   "max": str(max(row[index] for row in numeric_rows))}
            for index, axis in enumerate("XYZ")
        },
        "orden_cadenas_y_repeticiones_conservados": True,
        "origen_sin_modificaciones": True,
        "alcance": "POINT explícitos en ENTITIES de DXF ASCII; no es un conversor CAD general",
        "transformaciones": "ninguna; no se asignan ni convierten unidades o sistema de referencia",
    }
    # La creación exclusiva también protege ante una salida creada después de
    # la primera comprobación. No se reemplaza ningún archivo existente.
    with destination.open("xb") as target:
        target.write(output)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("entrada", type=Path, help="DXF ASCII con entidades POINT explícitas")
    parser.add_argument("salida", type=Path, help="CSV nuevo; no se reemplazan archivos existentes")
    parser.add_argument("--capa", help="Nombre exacto de la capa que se incluirá; por defecto todas")
    parser.add_argument("--sha256-esperado", help="SHA-256 esperado del DXF de entrada")
    parser.add_argument("--puntos-esperados", type=int, help="Recuento esperado de POINT incluidos")
    arguments = parser.parse_args()
    try:
        report = convert(arguments.entrada, arguments.salida, layer=arguments.capa,
                         expected_sha256=arguments.sha256_esperado, expected_points=arguments.puntos_esperados)
    except (ValueError, OSError) as error:
        detail = error.strerror if isinstance(error, OSError) else str(error)
        print(f"Error de conversión: {detail}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
