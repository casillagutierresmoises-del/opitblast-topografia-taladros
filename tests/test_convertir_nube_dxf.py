"""Conversión de nubes POINT con DXF sintéticos; no datos del taller."""

from contextlib import redirect_stderr, redirect_stdout
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "convertir_nube_dxf.py"
SPEC = importlib.util.spec_from_file_location("convertir_nube_dxf", SCRIPT)
converter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(converter)


def dxf(*entities):
    return ("0\nSECTION\n2\nENTITIES\n" + "".join(entities) + "0\nENDSEC\n0\nEOF\n").encode("ascii")


def point(x="1.000", y="2.00", z="3.0", layer="A"):
    return f"0\nPOINT\n8\n{layer}\n10\n{x}\n20\n{y}\n30\n{z}\n"


class DxfPointConversionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / "nube.dxf"
        self.output = self.folder / "puntos.csv"

    def test_preserves_decimal_strings_order_and_duplicates(self):
        payload = dxf(point(), point("-0.000", "4E+1", "0.1234567890123456789"), point())
        self.source.write_bytes(payload)
        result = converter.convert(self.source, self.output, expected_sha256=hashlib.sha256(payload).hexdigest(), expected_points=3)
        expected = "X,Y,Z\n1.000,2.00,3.0\n-0.000,4E+1,0.1234567890123456789\n1.000,2.00,3.0\n".encode()
        self.assertEqual(self.output.read_bytes(), expected)
        self.assertEqual(self.source.read_bytes(), payload)
        self.assertEqual(result["puntos_exportados"], 3)
        self.assertEqual(result["xyz_unicos"], 2)
        self.assertEqual(result["xyz_repetidos"], 1)
        self.assertEqual(result["sha256_salida"], hashlib.sha256(expected).hexdigest())
        self.assertNotIn(str(self.folder), json.dumps(result))

    def test_selects_exact_layer_and_ignores_other_entity_types(self):
        self.source.write_bytes(dxf(point(layer="A"), "0\nLINE\n10\n4\n20\n5\n30\n6\n", point("9", "8", "7", "B"), point(layer="A")))
        result = converter.convert(self.source, self.output, layer="B", expected_points=1)
        self.assertEqual(list(csv.reader(io.StringIO(self.output.read_text()))), [["X", "Y", "Z"], ["9", "8", "7"]])
        self.assertEqual(result["capas_detectadas"], {"A": 2, "B": 1})
        self.assertEqual(result["capas_incluidas"], {"B": 1})
        self.assertEqual(result["otras_entidades_omitidas"], {"LINE": 1})

    def test_existing_output_and_input_alias_are_never_replaced(self):
        payload = dxf(point())
        self.source.write_bytes(payload)
        self.output.write_bytes(b"conservar")
        with self.assertRaisesRegex(ValueError, "ya existe"):
            converter.convert(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), b"conservar")
        child = self.folder / "sub"
        child.mkdir()
        with self.assertRaisesRegex(ValueError, "distinta"):
            converter.convert(self.source, child / ".." / self.source.name)
        self.assertEqual(self.source.read_bytes(), payload)

    def test_malformed_or_unsupported_input_does_not_create_output(self):
        cases = {
            "binario": b"AutoCAD Binary DXF\r\n\x1a\0",
            "par incompleto": b"0\nSECTION\n2\n",
            "sin cierre": b"0\nSECTION\n2\nENTITIES\n" + point().encode(),
            "sin POINT": dxf("0\nLINE\n10\n1\n20\n2\n30\n3\n"),
            "sin Z explícita": dxf("0\nPOINT\n10\n1\n20\n2\n"),
            "NaN": dxf(point(z="NaN")),
            "coordenada repetida": dxf(point() + "10\n2\n"),
            "sección anidada": b"0\nSECTION\n2\nENTITIES\n0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF\n",
            "después de EOF": dxf(point()) + b"999\nextra\n",
            "código no numérico": dxf(point()).replace(b"10\n", b"abc\n"),
        }
        for name, payload in cases.items():
            with self.subTest(case=name):
                self.source.write_bytes(payload)
                with self.assertRaises(ValueError):
                    converter.convert(self.source, self.output)
                self.assertFalse(self.output.exists())
                self.assertEqual(self.source.read_bytes(), payload)

    def test_expected_hash_count_and_layer_are_checked_before_writing(self):
        self.source.write_bytes(dxf(point()))
        cases = [
            {"expected_sha256": "0" * 64},
            {"expected_points": 2},
            {"layer": "inexistente"},
            {"expected_sha256": "abc"},
            {"expected_points": 0},
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                converter.convert(self.source, self.output, **arguments)
            self.assertFalse(self.output.exists())

    def test_cli_outputs_json_with_only_basenames(self):
        self.source.write_bytes(dxf(point()))
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT), str(self.source), str(self.output)]), redirect_stdout(output), redirect_stderr(errors):
            status = converter.main()
        self.assertEqual(status, 0)
        self.assertEqual(errors.getvalue(), "")
        self.assertEqual(json.loads(output.getvalue())["fuente"], "nube.dxf")


if __name__ == "__main__":
    unittest.main()
