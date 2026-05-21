from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.vitaguide.converter import build_dataset, write_dataset
from src.vitaguide.engine import analyze, classify_severity


ROOT = Path(__file__).resolve().parents[1]
XLSX_PATH = ROOT / "TabelaInterações.xlsx"


class ConverterTests(unittest.TestCase):
    def test_build_dataset_extracts_items_and_external_catalog(self) -> None:
        dataset = build_dataset(XLSX_PATH)

        self.assertGreater(len(dataset["items"]), 0)
        self.assertGreater(len(dataset["external_catalog"]), 0)

        names = {item["name"] for item in dataset["items"]}
        self.assertIn("Vitamina A", names)
        self.assertIn("Ginkgo Biloba", names)

    def test_write_dataset_creates_valid_json(self) -> None:
        dataset = build_dataset(XLSX_PATH)

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "dataset.json"
            write_dataset(XLSX_PATH, output)

            self.assertTrue(output.exists())
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(written["version"], 1)
            self.assertEqual(len(written["items"]), len(dataset["items"]))


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = build_dataset(XLSX_PATH)

    def test_classify_severity_prioritizes_contraindication(self) -> None:
        self.assertEqual(classify_severity("qualquer texto", "contraindicacoes"), "contraindicacao")
        self.assertEqual(classify_severity("risco de sangramento", "interacoes"), "grave")
        self.assertEqual(classify_severity("precaucao em doentes", "interacoes"), "moderada")

    def test_analyze_returns_known_findings_for_real_dataset(self) -> None:
        result = analyze(
            self.dataset,
            ["Vitamina E", "Vitamina K"],
            ["varfarina"],
            "metformina",
        )

        self.assertEqual(result["selected_supplements"], ["Vitamina E", "Vitamina K"])
        self.assertIn("metformina", result["unknown_external_terms"])

        categories = [finding["category"] for finding in result["findings"]]
        self.assertIn("contraindicacoes", categories)
        self.assertIn("efeitos_adversos", categories)

        self.assertTrue(
            any(
                "varfarina" in {match.lower() for match in finding["matched_externals"]}
                for finding in result["findings"]
            )
        )

    def test_analyze_deduplicates_free_text_terms(self) -> None:
        result = analyze(self.dataset, ["Vitamina E"], ["Varfarina", "varfarina"], "varfarina; metformina")

        normalized = [term.lower() for term in result["selected_externals"]]
        self.assertEqual(normalized.count("varfarina"), 1)


if __name__ == "__main__":
    unittest.main()