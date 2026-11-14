"""Parity tests: every Python output must match the R output.

Runs the Python pipeline fresh, writes its outputs to a temporary folder, reads them
back, and compares each with the CSV written by r/pipeline.R. Both sides go through
a CSV round trip, so the comparison is like for like.

Run from the repository root:  uv run pytest
"""
from pathlib import Path

import pandas as pd
import pytest

import pipeline

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ["match_data", "round_summary", "phase_summary"]


@pytest.fixture(scope="module")
def py_dir(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("py_outputs")
    pipeline.write_outputs(pipeline.run(ROOT / "data" / "raw_results.csv"), out_dir)
    return out_dir


@pytest.mark.parametrize("name", OUTPUTS)
def test_python_matches_r(py_dir, name):
    r_df = pd.read_csv(ROOT / "r_outputs" / f"{name}.csv")
    py_df = pd.read_csv(py_dir / f"{name}.csv")

    assert list(py_df.columns) == list(r_df.columns), "column names or order differ"
    assert len(py_df) == len(r_df), f"row counts differ: Python {len(py_df)}, R {len(r_df)}"
    pd.testing.assert_frame_equal(py_df, r_df, check_dtype=False, check_exact=False, rtol=1e-9)
