"""
Evaluation runner for the AI Debugging Agent.

Resets logic_utils.py to the broken state before each trial, runs the agent,
and records outcome, iteration count, and elapsed time. Prints a summary and
saves a JSON report to eval/results.json.

Usage (run from project root):
    python eval/evaluate.py           # 3 trials (default)
    python eval/evaluate.py --runs 5
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from agent.debugger_agent import reset_to_broken, run_debugger_agent


def _parse_test_counts(test_output: str) -> tuple[int, int]:
    """Return (passed, failed) counts extracted from pytest stdout."""
    passed = failed = 0
    for line in test_output.splitlines():
        parts = line.split()
        for i, part in enumerate(parts):
            if part == "passed" and i > 0:
                try:
                    passed = int(parts[i - 1])
                except ValueError:
                    pass
            if part == "failed" and i > 0:
                try:
                    failed = int(parts[i - 1])
                except ValueError:
                    pass
    return passed, failed


def run_evaluation(n_runs: int) -> dict:
    print(f"\nAI Debugging Agent — Evaluation ({n_runs} trial{'s' if n_runs != 1 else ''})\n")
    print(f"{'Trial':<8} {'Status':<10} {'Iterations':<12} {'Time':>8}  {'Tests'}")
    print("-" * 55)

    trials = []

    for i in range(1, n_runs + 1):
        reset_to_broken()
        start = time.time()

        result = run_debugger_agent()  # no UI callback; output goes to agent_run.log

        elapsed = round(time.time() - start, 1)
        passed, failed = _parse_test_counts(result["test_output"])

        trial = {
            "trial": i,
            "status": result["status"],
            "iterations": result["iterations"],
            "time_seconds": elapsed,
            "tests_passed": passed,
            "tests_failed": failed,
            "error": result.get("error"),
        }
        trials.append(trial)

        icon = "✅" if result["status"] == "success" else ("⚠️ " if result["status"] == "partial" else "❌")
        print(
            f"{i:<8} {icon + result['status']:<12} {result['iterations']:<12} {elapsed:>6}s"
            f"  {passed} passed, {failed} failed"
        )

    # ── summary stats ──────────────────────────────────────────────────────────
    successes = sum(1 for t in trials if t["status"] == "success")
    avg_iters = round(sum(t["iterations"] for t in trials) / len(trials), 2)
    avg_time = round(sum(t["time_seconds"] for t in trials) / len(trials), 1)
    total_passed = sum(t["tests_passed"] for t in trials)
    total_tests = total_passed + sum(t["tests_failed"] for t in trials)

    report = {
        "timestamp": datetime.now().isoformat(),
        "model": "llama3.2",
        "runs": n_runs,
        "success_rate": f"{successes}/{n_runs}",
        "avg_iterations_to_fix": avg_iters,
        "avg_time_seconds": avg_time,
        "total_test_assertions": total_tests,
        "total_assertions_passed": total_passed,
        "trials": trials,
    }

    report_path = ROOT / "eval" / "results.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"""
Summary
-------
Success rate:           {successes}/{n_runs} ({round(successes / n_runs * 100)}%)
Avg iterations to fix:  {avg_iters}
Avg time per run:       {avg_time}s
Test assertions:        {total_passed}/{total_tests} passed across all trials
Report saved:           eval/results.json
""")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the AI Debugging Agent")
    parser.add_argument(
        "--runs", type=int, default=3,
        help="Number of evaluation trials to run (default: 3)"
    )
    args = parser.parse_args()
    run_evaluation(args.runs)
