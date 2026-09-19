import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import run


class RunnerChecks(unittest.TestCase):
    def observation(self):
        return {
            "diagnostics": [], "missing": {}, "extra": {}, "outside": [],
            "required_log_present": True,
        }

    def case(self):
        return {"kind": "pass", "max_runs": 2}

    def test_advisory_requires_explicit_selection(self):
        cases = [{"id": "ordinary"}, {"id": "unsupported", "advisory": True}]
        self.assertEqual(run.select_cases(cases, None), cases[:1])
        self.assertEqual(run.select_cases(cases, ["unsupported"]), cases[1:])

    def test_invalid_or_duplicate_selection_is_rejected(self):
        cases = [{"id": "ordinary"}]
        for selected in [["unknown"], ["ordinary", "ordinary"]]:
            with self.assertRaises(ValueError):
                run.select_cases(cases, selected)
        with self.assertRaises(ValueError):
            run.select_cases(cases * 2, None)

    def test_compressed_reference_preserves_unicode_and_numbers(self):
        expected = {"name": "目錄", "box": [0.0, 12.375], "text": "A\nB"}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "reference.json.gz"
            path.write_bytes(gzip.compress(json.dumps(expected).encode(), mtime=0))
            self.assertEqual(run.read_json(path), expected)

    def test_each_required_observation_is_compared(self):
        expected = {"pages": [{"words": [["entry", 1.0, 2.0, 3.0, 4.0]]}],
                    "raster": ["rgb"], "aux": {"aux": "hash"},
                    "effects": {"nodes": "hash"}, "log_events": ["formatted=1"]}
        for key in expected:
            changed = copy.deepcopy(expected)
            changed[key] = []
            self.assertEqual(run.compare(changed, expected), [key])
        changed = copy.deepcopy(expected)
        changed["unexpected"] = True
        self.assertEqual(run.compare(changed, expected), ["unexpected"])

    def test_missing_duplicate_and_offpage_nodes_fail(self):
        for key in ("missing", "extra", "outside"):
            obs = self.observation()
            obs[key] = ["entry"]
            self.assertIn(key, run.validate(obs, self.case(), 0, True, 2, "pdflatex"))

    def test_convergence_and_compile_status_fail(self):
        for code, stable, runs in [(1, True, 2), (0, False, 2), (0, True, 3)]:
            self.assertTrue(run.validate(self.observation(), self.case(), code, stable, runs, "pdflatex"))

    def test_diagnostics_are_exact_and_engine_specific(self):
        obs = self.observation()
        obs["diagnostics"] = ["Overfull \\vbox (44.0pt too high)"]
        self.assertTrue(run.validate(obs, self.case(), 0, True, 2, "pdflatex"))
        case = self.case()
        case["expected_diagnostics"] = {"pdflatex": obs["diagnostics"]}
        self.assertEqual(run.validate(obs, case, 0, True, 2, "pdflatex"), [])
        obs["diagnostics"] = []
        self.assertTrue(run.validate(obs, case, 0, True, 2, "pdflatex"))

    def test_guard_requires_fatal_status_exact_count_and_diagnostic(self):
        case = {"kind": "expected-error", "retry_attempts": 20}
        good = {"error_present": True, "required_log_present": True,
                "diagnostic_count": 1, "retries": list(range(1, 21))}
        self.assertEqual(run.validate(good, case, 1, False, 1, "pdflatex"), [])
        for field, value in [("retries", list(range(1, 20))),
                             ("retries", list(range(1, 22))),
                             ("diagnostic_count", 2), ("error_present", False)]:
            obs = dict(good, **{field: value})
            self.assertTrue(run.validate(obs, case, 1, False, 1, "pdflatex"))
        self.assertTrue(run.validate(good, case, 0, False, 1, "pdflatex"))

    def test_final_rerun_or_missing_glyph_cannot_pass_as_stable(self):
        for line in ["Package dirtreex Warning: Rerun LaTeX to get dirtreex page breaks right.",
                     "LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.",
                     "LaTeX Warning: There were undefined references.",
                     "Missing character: There is no X in font nullfont!"]:
            self.assertTrue(run.final_log_errors(line))
        self.assertEqual(run.final_log_errors("Output written on input.pdf (3 pages)."), [])


if __name__ == "__main__":
    unittest.main()
