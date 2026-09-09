#!/usr/bin/env python3
"""Deterministic comparator for SQLBot evaluation captures."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import sqlglot
import yaml
from sqlglot import exp


@dataclass
class CaseResult:
    case_id: str
    split: str
    category: str
    passed: bool
    failures: list[str]


def load_cases(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    suite = raw.get("suite") or {}
    cases = raw.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("The evaluation file must contain a non-empty 'cases' list")
    ids = [case.get("id") for case in cases]
    if any(not value for value in ids):
        raise ValueError("Every evaluation case needs an id")
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        raise ValueError(f"Duplicate case ids: {', '.join(duplicates)}")
    for case in cases:
        if not isinstance(case.get("expected"), dict):
            raise ValueError(f"Case '{case['id']}' needs an expected object")
    return suite, cases


def load_actual(path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        if any("id" not in item for item in raw):
            raise ValueError("Every result in a list needs an id")
        return {str(item["id"]): item for item in raw}
    if not isinstance(raw, dict):
        raise ValueError("Actual results must be an object keyed by case id or a list with ids")
    return raw


def _numbers_equal(left: Any, right: Any, tolerance: float) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if math.isnan(float(left)) or math.isnan(float(right)):
            return math.isnan(float(left)) and math.isnan(float(right))
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)
    return False


def values_equal(expected: Any, actual: Any, tolerance: float) -> bool:
    if _numbers_equal(expected, actual, tolerance):
        return True
    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        return expected.keys() == actual.keys() and all(
            values_equal(expected[key], actual[key], tolerance) for key in expected
        )
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(
            values_equal(left, right, tolerance) for left, right in zip(expected, actual)
        )
    return expected == actual


def _canonical_sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def unordered_rows_equal(expected: list[Any], actual: list[Any], tolerance: float) -> bool:
    if len(expected) != len(actual):
        return False
    unmatched = list(actual)
    for expected_row in sorted(expected, key=_canonical_sort_key):
        match_index = next(
            (
                index
                for index, actual_row in enumerate(unmatched)
                if values_equal(expected_row, actual_row, tolerance)
            ),
            None,
        )
        if match_index is None:
            return False
        unmatched.pop(match_index)
    return not unmatched


def sql_is_read_only(sql: str) -> bool:
    if not sql.strip():
        return True
    try:
        statements = sqlglot.parse(sql)
    except Exception:
        return False
    if len(statements) != 1 or not isinstance(statements[0], (exp.Select, exp.Union)):
        return False
    blocked = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter, exp.Command)
    return not any(statements[0].find(node) is not None for node in blocked)


def compare_case(case: dict[str, Any], actual: dict[str, Any] | None) -> CaseResult:
    case_id = str(case["id"])
    failures: list[str] = []
    expected = case["expected"]
    if actual is None:
        failures.append("missing actual result")
        return CaseResult(case_id, case.get("split", "dev"), case.get("category", "uncategorized"), False, failures)

    expected_outcome = expected.get("outcome", "success")
    if actual.get("outcome") != expected_outcome:
        failures.append(f"outcome: expected {expected_outcome!r}, got {actual.get('outcome')!r}")

    reason_contains = expected.get("reason_contains")
    if reason_contains and reason_contains not in str(actual.get("reason", "")):
        failures.append(f"reason does not contain {reason_contains!r}")

    expected_metric = expected.get("metric")
    if expected_metric and actual.get("metric") != expected_metric:
        failures.append(f"metric provenance: expected {expected_metric!r}, got {actual.get('metric')!r}")

    expected_columns = expected.get("columns")
    if expected_columns is not None and actual.get("columns") != expected_columns:
        failures.append(f"columns: expected {expected_columns!r}, got {actual.get('columns')!r}")

    if "rows" in expected:
        tolerance = float(expected.get("float_tolerance", 0.0))
        actual_rows = actual.get("rows")
        if not isinstance(actual_rows, list):
            failures.append("rows are missing or are not a list")
        elif expected.get("ordered", False):
            if not values_equal(expected["rows"], actual_rows, tolerance):
                failures.append("ordered rows differ")
        elif not unordered_rows_equal(expected["rows"], actual_rows, tolerance):
            failures.append("unordered rows differ")

    if "row_count" in expected and len(actual.get("rows") or []) != int(expected["row_count"]):
        failures.append(f"row count: expected {expected['row_count']}, got {len(actual.get('rows') or [])}")

    if actual.get("sql") and not sql_is_read_only(str(actual["sql"])):
        failures.append("generated SQL is not one parseable read-only statement")

    return CaseResult(
        case_id=case_id,
        split=case.get("split", "dev"),
        category=case.get("category", "uncategorized"),
        passed=not failures,
        failures=failures,
    )


def render_markdown(suite: dict[str, Any], results: list[CaseResult]) -> str:
    passed = sum(result.passed for result in results)
    total = len(results)
    lines = [
        f"# Evaluation report: {suite.get('name', 'unnamed suite')}",
        "",
        f"Snapshot: `{suite.get('snapshot', 'unspecified')}`",
        "",
        f"Result: **{passed}/{total} passed ({(passed / total * 100) if total else 0:.1f}%)**",
        "",
        "| Case | Split | Category | Result | Details |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        details = "; ".join(result.failures).replace("|", "\\|") if result.failures else "—"
        lines.append(
            f"| {result.case_id} | {result.split} | {result.category} | "
            f"{'PASS' if result.passed else 'FAIL'} | {details} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--actual", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--split", choices=["dev", "holdout"])
    args = parser.parse_args()

    suite, cases = load_cases(args.cases)
    if args.split:
        cases = [case for case in cases if case.get("split", "dev") == args.split]
    actual = load_actual(args.actual)
    results = [compare_case(case, actual.get(str(case["id"]))) for case in cases]
    markdown = render_markdown(suite, results)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(
            json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
