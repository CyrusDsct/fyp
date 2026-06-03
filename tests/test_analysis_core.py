from __future__ import annotations

import unittest

from backend.analysis_core import (
    attach_input_context,
    load_prompt_template,
    normalize_range_value_to_intervals,
    parse_model_json,
    unwrap_analysis_json,
)


class AnalysisCoreTests(unittest.TestCase):
    def test_default_prompt_path_loads(self) -> None:
        self.assertGreater(len(load_prompt_template()), 100)

    def test_parse_model_json_extracts_json_from_text(self) -> None:
        parsed = parse_model_json('prefix {"status": "ok", "score": 1} suffix')
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["score"], 1)

    def test_normalize_range_edges_to_intervals(self) -> None:
        intervals = normalize_range_value_to_intervals([0, 10, 20])
        self.assertEqual(intervals, [[0.0, 10.0], [10.0, 20.0]])

    def test_unwrap_analysis_json(self) -> None:
        wrapped = {"choropleth_map_evaluation": {"quality": "good"}}
        self.assertEqual(unwrap_analysis_json(wrapped), {"quality": "good"})

    def test_attach_input_context_fills_unknowns(self) -> None:
        result = attach_input_context({}, "", "Show population", "")
        self.assertEqual(result["input_context"]["audience"], "unknown")
        self.assertEqual(result["input_context"]["purpose"], "Show population")
        self.assertEqual(result["input_context"]["distribution"], "unknown")


if __name__ == "__main__":
    unittest.main()
