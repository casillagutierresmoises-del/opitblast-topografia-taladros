"""Regresiones del verificador con datos sintéticos, sin archivos del taller."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verificar_geometria.py"
SPEC = importlib.util.spec_from_file_location("verificar_geometria", SCRIPT)
verifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verifier
SPEC.loader.exec_module(verifier)


class GeometryVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / "fuente.csv"
        self.holes = self.folder / "segmentos.csv"
        self.pattern = self.folder / "malla.csv"
        self.export = self.folder / "segmentos_exportados.csv"
        self.points = self.folder / "puntos_exportados.csv"
        self.indices = self.folder / "indices.csv"
        self.holes.write_text("X,Y,Z,X_Toe,Y_Toe,Z_Toe\n0.250,0.250,1.000,0.250,0.250,0.000\n", encoding="utf-8")
        self.pattern.write_text("ID,ESTE,NORTE,ELEV\nA,99.000,99.000,1.000\n", encoding="utf-8")
        self.export.write_text(self.holes.read_text(encoding="utf-8").replace("Z_Toe\n", "Z_Toe,LENGTH\n").replace("0.000\n", "0.000,1.000\n"), encoding="utf-8")
        self.write_terrain(
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 0)], [(0, 1, 2)]
        )

    def write_terrain(self, points, faces):
        coordinates = "X,Y,Z\n" + "".join(",".join(f"{value:.3f}" for value in point) + "\n" for point in points)
        self.source.write_text(coordinates, encoding="utf-8")
        self.points.write_text(coordinates, encoding="utf-8")
        self.indices.write_text("T1,T2,T3\n" + "".join(",".join(map(str, face)) + "\n" for face in faces), encoding="utf-8")

    def run_cli(self, *extra):
        output, errors = io.StringIO(), io.StringIO()
        args = [str(SCRIPT), str(self.source), str(self.holes), str(self.pattern), *map(str, extra)]
        with patch.object(sys, "argv", args), redirect_stdout(output), redirect_stderr(errors):
            status = verifier.main()
        return status, output.getvalue(), errors.getvalue()

    def topology_cli(self):
        status, output, errors = self.run_cli(
            "--terreno-exportado", self.points, "--indices-exportados", self.indices
        )
        self.assertEqual(errors, "")
        return status, json.loads(output)["verificacion_topografia_nativa"]

    def test_output_cannot_overwrite_any_required_or_optional_input(self):
        inputs = [self.source, self.holes, self.pattern, self.export, self.points, self.indices]
        original_bytes = {path: path.read_bytes() for path in inputs}
        for output_path in inputs:
            with self.subTest(input=output_path.name):
                status, output, errors = self.run_cli(
                    "--exportacion", self.export,
                    "--terreno-exportado", self.points, "--indices-exportados", self.indices,
                    "--salida", output_path,
                )
                self.assertEqual(status, 2)
                self.assertEqual(output, "")
                self.assertIn("archivo distinto", errors)
                self.assertEqual({path: path.read_bytes() for path in inputs}, original_bytes)

    def test_output_alias_is_resolved_before_writing(self):
        child = self.folder / "subcarpeta"
        child.mkdir()
        alias = child / ".." / self.source.name
        original = self.source.read_bytes()
        status, _, errors = self.run_cli("--salida", alias)
        self.assertEqual(status, 2)
        self.assertIn("archivo distinto", errors)
        self.assertEqual(self.source.read_bytes(), original)

    def test_output_hardlink_cannot_replace_input(self):
        alias = self.folder / "alias.json"
        try:
            os.link(self.source, alias)
        except OSError as error:
            self.skipTest(f"Este sistema no permite enlaces duros: {error}")
        original = self.source.read_bytes()
        status, _, errors = self.run_cli("--salida", alias)
        self.assertEqual(status, 2)
        self.assertIn("archivo distinto", errors)
        self.assertEqual(self.source.read_bytes(), original)

    def test_unused_duplicate_vertex_is_allowed_when_all_unique_sites_are_used(self):
        status, result = self.topology_cli()
        self.assertEqual(status, 0)
        self.assertTrue(result["coincidencia_a_precision_exportada"])
        self.assertTrue(result["triangulacion_pasa_controles_basicos"])
        self.assertEqual(result["vertices_no_referenciados"], 1)
        self.assertEqual(result["sitios_xyz_sin_caras"], 0)

    def test_matching_coordinates_do_not_accept_invalid_triangulation(self):
        cases = [
            ("cara duplicada", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2), (2, 1, 0)], "caras_repetidas_sin_orientacion", 1),
            ("índices repetidos", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 1)], "caras_con_indices_repetidos", 1),
            ("área cero", [(0, 0, 0), (1, 0, 0), (2, 0, 0)], [(0, 1, 2)], "caras_area_cero_segun_puntos_exportados", 1),
            ("sitio sin cara", [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)], [(0, 1, 2)], "sitios_xyz_sin_caras", 1),
            ("índice fuera de rango", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 99)], "base_indices_demostrada", None),
        ]
        for name, points, faces, metric, expected in cases:
            with self.subTest(case=name):
                self.write_terrain(points, faces)
                status, result = self.topology_cli()
                self.assertEqual(status, 2)
                self.assertTrue(result["coincidencia_a_precision_exportada"])
                self.assertFalse(result["triangulacion_pasa_controles_basicos"])
                self.assertEqual(result[metric], expected)


if __name__ == "__main__":
    unittest.main()
