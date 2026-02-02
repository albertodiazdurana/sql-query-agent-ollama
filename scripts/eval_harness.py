"""EXP-001 Evaluation Harness

Reusable evaluation framework for text-to-SQL model comparison.
Extracted from notebook Cell 28 for reproducibility and script-based execution.

Design decisions documented in: data/experiments/s01_d02_exp001/README.md (ED-1, ED-2, ED-3)
"""

import time
import json
import sqlglot
from dataclasses import dataclass, asdict
from typing import Any, Optional
from pathlib import Path


@dataclass
class EvalResult:
    """Single query evaluation result for EXP-001."""
    query_id: str
    difficulty: str
    question: str
    model: str
    raw_sql: Optional[str] = None
    final_sql: Optional[str] = None
    raw_parsable: bool = False
    effectively_parsable: bool = False
    execution_accurate: bool = False
    post_processing_applied: bool = False
    retry_count: int = 0
    latency_seconds: float = 0.0
    actual_result: Any = None
    error: Optional[str] = None
    error_category: Optional[str] = None


def check_sql_parsable(sql: str) -> bool:
    """Check if SQL parses with sqlglot."""
    if not sql or not sql.strip():
        return False
    try:
        result = sqlglot.parse(sql)
        return len(result) > 0 and result[0] is not None
    except Exception:
        return False


def to_plain(val):
    """Convert SQLAlchemy Row objects to plain Python types."""
    if val is None:
        return None
    if hasattr(val, '_mapping'):
        return tuple(val)
    if isinstance(val, list):
        return [to_plain(v) for v in val]
    if isinstance(val, tuple):
        return tuple(to_plain(v) for v in val)
    return val


def values_match(a, e) -> bool:
    """Compare two values with float tolerance (0.01 for aggregation results)."""
    if isinstance(a, float) and isinstance(e, float):
        return abs(a - e) < 0.01
    return a == e


def compare_results(actual, expected, query_id: str) -> bool:
    """Compare agent output to ground truth.

    ED-2: Flexible comparison adapting the Spider EX metric.
    GT formats:
    - Scalar int/float: count queries (E1, E4) or row-count checks (E2, H2)
    - Tuple: single-row result (E3, M1)
    - List: multi-row result (E5, M2-M5, H1, H3, H4)

    For scalar GT with list actual:
    - If actual is [(N,)] (1 row, 1 col): compare N to GT (count query)
    - If actual is [row, row, ...]: compare len to GT (row count)
    """
    if actual is None:
        return False

    actual = to_plain(actual)
    expected = to_plain(expected)

    if expected is None:
        return False

    # --- Scalar GT ---
    if isinstance(expected, (int, float)):
        if isinstance(actual, list):
            if len(actual) == 0:
                return False
            if len(actual) == 1:
                row = actual[0]
                if isinstance(row, (list, tuple)) and len(row) == 1:
                    return values_match(row[0], expected)
            # Multi-row result: compare row count
            return len(actual) == expected
        return values_match(actual, expected)

    # --- Tuple GT (single row) ---
    if isinstance(expected, tuple):
        if isinstance(actual, list) and len(actual) >= 1:
            row = actual[0]
            if not isinstance(row, (list, tuple)):
                row = (row,)
            return all(values_match(a, e) for a, e in zip(row, expected))
        return False

    # --- List GT (multi-row) ---
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        if len(actual) != len(expected):
            return False
        if len(expected) > 0 and len(actual) > 0:
            a_row = actual[0] if isinstance(actual[0], (list, tuple)) else (actual[0],)
            e_row = expected[0] if isinstance(expected[0], (list, tuple)) else (expected[0],)
            if not all(values_match(a, e) for a, e in zip(a_row, e_row)):
                return False
        return True

    return False


def categorize_error(er: EvalResult) -> str:
    """Assign error category per EXP-001 protocol.

    ED-3: Priority order — schema_linking > syntax > dialect > hallucination > logic > unknown.
    """
    err = (er.error or "").lower()
    if "no such column" in err or "ambiguous" in err:
        return "schema_linking"
    if er.raw_sql and not er.raw_parsable:
        return "syntax"
    if er.post_processing_applied and not er.effectively_parsable:
        return "dialect"
    if "no such table" in err:
        return "hallucination"
    if er.effectively_parsable:
        return "logic"
    return "unknown"


def run_evaluation(model_name: str, test_suite: list, ground_truth: dict,
                   graph, verbose: bool = True) -> list:
    """Run EXP-001 evaluation for one model on the full test suite.

    ED-1: Uses graph.stream() to capture raw SQL from generate_sql node
    before post-processing, alongside final execution results.

    Args:
        model_name: Ollama model identifier (e.g. 'sqlcoder:7b')
        test_suite: List of TestQuery objects
        ground_truth: Dict mapping query_id -> expected result
        graph: Compiled LangGraph StateGraph
        verbose: Print per-query progress

    Returns:
        List of EvalResult objects
    """
    eval_results = []

    if verbose:
        print(f"\n{'='*70}")
        print(f"  EXP-001 EVALUATION: {model_name}")
        print(f"  {len(test_suite)} queries | temp=0 | max_retries=3")
        print(f"{'='*70}")

    for i, tq in enumerate(test_suite):
        if verbose:
            print(f"\n[{tq.id}] ({i+1}/{len(test_suite)}) {tq.difficulty}")
            print(f"  Q: {tq.question}")

        er = EvalResult(
            query_id=tq.id, difficulty=tq.difficulty,
            question=tq.question, model=model_name
        )

        initial_state = {
            "question": tq.question,
            "model_name": model_name,
            "retry_count": 0,
            "relevant_tables": [],
            "schema_text": "",
            "generated_sql": "",
            "is_valid": False,
            "validation_error": "",
            "results": None,
            "error": "",
        }

        start = time.time()
        try:
            raw_sql_captured = None
            final_state = {}

            for event in graph.stream(initial_state):
                for node_name, update in event.items():
                    if node_name == "generate_sql":
                        raw_sql_captured = update.get("generated_sql")
                    final_state.update(update)

            er.latency_seconds = time.time() - start
            er.raw_sql = raw_sql_captured
            er.final_sql = final_state.get("generated_sql")
            er.actual_result = final_state.get("results")
            er.error = final_state.get("error") or None
            er.retry_count = final_state.get("retry_count", 0)

            # Metrics
            er.raw_parsable = check_sql_parsable(er.raw_sql) if er.raw_sql else False
            er.effectively_parsable = (
                er.actual_result is not None and not er.error
            )
            er.post_processing_applied = (
                er.raw_sql is not None
                and er.final_sql is not None
                and er.raw_sql.strip() != er.final_sql.strip()
            )
            er.execution_accurate = compare_results(
                er.actual_result, ground_truth.get(tq.id), tq.id
            )
            if not er.execution_accurate:
                er.error_category = categorize_error(er)

        except Exception as exc:
            er.latency_seconds = time.time() - start
            er.error = str(exc)
            er.error_category = "runtime"

        eval_results.append(er)

        # Per-query output
        if verbose:
            tag = "PASS" if er.execution_accurate else "FAIL"
            print(f"  {tag} | retries={er.retry_count} | {er.latency_seconds:.1f}s"
                  f" | pp={'Y' if er.post_processing_applied else 'N'}")
            if er.final_sql:
                print(f"  SQL: {er.final_sql.replace(chr(10), ' ')[:75]}")
            if not er.execution_accurate:
                cat = er.error_category or "?"
                err_msg = f" — {er.error[:55]}" if er.error else ""
                print(f"  [{cat}]{err_msg}")

    # Aggregate metrics
    n = len(eval_results)
    metrics = {
        "Execution Accuracy (EX)": sum(r.execution_accurate for r in eval_results),
        "Raw Parsability":         sum(r.raw_parsable for r in eval_results),
        "Effective Parsability":   sum(r.effectively_parsable for r in eval_results),
        "Retry Rate":              sum(r.retry_count > 0 for r in eval_results),
        "Post-Processing Rate":    sum(r.post_processing_applied for r in eval_results),
    }
    avg_latency = sum(r.latency_seconds for r in eval_results) / n if n else 0

    if verbose:
        print(f"\n{'='*70}")
        print(f"  RESULTS: {model_name}")
        print(f"  {'─'*66}")
        for name, count in metrics.items():
            print(f"  {name:<28s} {count:>2}/{n}  ({count/n*100:5.1f}%)")
        print(f"  {'Avg Latency':<28s} {avg_latency:>6.1f}s")

        # Per-difficulty breakdown
        print(f"  {'─'*66}")
        for diff in ["Easy", "Medium", "Hard"]:
            subset = [r for r in eval_results if r.difficulty == diff]
            if subset:
                ex = sum(r.execution_accurate for r in subset)
                lat = sum(r.latency_seconds for r in subset) / len(subset)
                print(f"  {diff:<8s} EX={ex}/{len(subset)}  Avg latency={lat:.1f}s")
        print(f"{'='*70}")

    return eval_results


def save_results(eval_results: list, output_path: Path) -> None:
    """Save evaluation results to JSON for later analysis."""
    data = {
        "model": eval_results[0].model if eval_results else "unknown",
        "n_queries": len(eval_results),
        "summary": {
            "execution_accuracy": sum(r.execution_accurate for r in eval_results),
            "raw_parsability": sum(r.raw_parsable for r in eval_results),
            "effective_parsability": sum(r.effectively_parsable for r in eval_results),
            "retry_rate": sum(r.retry_count > 0 for r in eval_results),
            "post_processing_rate": sum(r.post_processing_applied for r in eval_results),
            "avg_latency": sum(r.latency_seconds for r in eval_results) / len(eval_results)
                if eval_results else 0,
        },
        "per_difficulty": {},
        "results": [],
    }

    for diff in ["Easy", "Medium", "Hard"]:
        subset = [r for r in eval_results if r.difficulty == diff]
        if subset:
            data["per_difficulty"][diff] = {
                "n": len(subset),
                "execution_accuracy": sum(r.execution_accurate for r in subset),
                "avg_latency": sum(r.latency_seconds for r in subset) / len(subset),
            }

    for r in eval_results:
        data["results"].append({
            "query_id": r.query_id,
            "difficulty": r.difficulty,
            "question": r.question,
            "model": r.model,
            "raw_sql": r.raw_sql,
            "final_sql": r.final_sql,
            "raw_parsable": r.raw_parsable,
            "effectively_parsable": r.effectively_parsable,
            "execution_accurate": r.execution_accurate,
            "post_processing_applied": r.post_processing_applied,
            "retry_count": r.retry_count,
            "latency_seconds": round(r.latency_seconds, 2),
            "actual_result": _serialize_result(r.actual_result),
            "error": r.error,
            "error_category": r.error_category,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {output_path}")


def _serialize_result(result):
    """Convert result to JSON-serializable format."""
    if result is None:
        return None
    if isinstance(result, list):
        return [_serialize_result(r) for r in result]
    if isinstance(result, tuple):
        return list(result)
    if hasattr(result, '_mapping'):
        return list(result)
    return result
