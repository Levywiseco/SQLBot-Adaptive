import importlib.util
import sys
from pathlib import Path

RUNNER_PATH = Path(__file__).resolve().parents[1] / "evaluations" / "run.py"
SPEC = importlib.util.spec_from_file_location("adaptive_evaluation_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def test_unordered_rows_use_numeric_tolerance():
    expected = [{"region": "east", "value": 100.0}, {"region": "west", "value": 40.0}]
    actual = [{"region": "west", "value": 40.004}, {"region": "east", "value": 100}]
    assert runner.unordered_rows_equal(expected, actual, 0.01)


def test_nested_values_do_not_ignore_column_differences():
    assert not runner.values_equal({"amount": 10}, {"total": 10}, 0.01)


def test_sql_read_only_check_rejects_multiple_or_mutating_statements():
    assert runner.sql_is_read_only("SELECT region, SUM(amount) FROM sales GROUP BY region")
    assert not runner.sql_is_read_only("SELECT 1; DROP TABLE sales")
    assert not runner.sql_is_read_only("DELETE FROM sales")


def test_metric_provenance_is_part_of_case_result():
    case = {
        "id": "metric-version",
        "split": "holdout",
        "category": "metric",
        "expected": {
            "outcome": "success",
            "metric": {"code": "net_sales", "version": 2},
        },
    }
    result = runner.compare_case(
        case,
        {"outcome": "success", "metric": {"code": "net_sales", "version": 1}},
    )
    assert not result.passed
    assert "metric provenance" in result.failures[0]
