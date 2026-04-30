"""
AI Debugging Agent — agentic loop that reads broken code, identifies bugs,
generates fixes, runs pytest, and iterates until all tests pass.

Uses the native Ollama Python client. No API key required.
Default model: llama3.2. Change OLLAMA_MODEL to swap models.
"""

import logging
import subprocess
import sys
from pathlib import Path

import ollama

from agent.prompts import (
    ANALYZE_SYSTEM,
    ANALYZE_USER,
    ERROR_SECTION,
    FIX_SYSTEM,
    FIX_USER,
)

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
BROKEN_LOGIC_PATH = ROOT / "broken_game" / "broken_logic.py"
TARGET_PATH = ROOT / "logic_utils.py"
TESTS_PATH = ROOT / "tests"
LOG_PATH = ROOT / "agent_run.log"

MAX_ITERATIONS = 3
OLLAMA_MODEL = "llama3.2"

# ── logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)


# ── helpers ────────────────────────────────────────────────────────────────────

def _get_client() -> ollama.Client:
    """Return a native Ollama client."""
    return ollama.Client()


def _strip_fences(text: str) -> str:
    """Remove accidental markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop opening fence line and closing fence line if present
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()
    return text


def _run_pytest() -> tuple[bool, str]:
    """Run the test suite and return (all_passed, combined_output)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(TESTS_PATH), "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    output = result.stdout + result.stderr
    logger.info("pytest exit code %d\n%s", result.returncode, output)
    return result.returncode == 0, output


# ── agent phases ───────────────────────────────────────────────────────────────

def _analyze_bugs(client: ollama.Client, code: str, token_cb=None) -> str:
    logger.info("Phase PLAN: calling %s for bug analysis", OLLAMA_MODEL)
    stream = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": ANALYZE_SYSTEM},
            {"role": "user", "content": ANALYZE_USER.format(code=code)},
        ],
        stream=True,
    )
    analysis = ""
    for chunk in stream:
        analysis += chunk.message.content
        if token_cb:
            token_cb(analysis)
    logger.info("Bug analysis:\n%s", analysis)
    return analysis


def _generate_fix(
    client: ollama.Client,
    broken_code: str,
    bug_analysis: str,
    test_error: str | None,
    token_cb=None,
) -> str:
    logger.info("Phase FIX: calling %s to generate corrected code", OLLAMA_MODEL)
    error_section = ERROR_SECTION.format(test_error=test_error) if test_error else ""
    prompt = FIX_USER.format(
        broken_code=broken_code,
        bug_analysis=bug_analysis,
        error_section=error_section,
    )
    stream = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": FIX_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    fixed = ""
    for chunk in stream:
        fixed += chunk.message.content
        if token_cb:
            token_cb(fixed)
    fixed = _strip_fences(fixed)
    logger.info("Fix generated (%d chars)", len(fixed))
    return fixed


# ── public API ─────────────────────────────────────────────────────────────────

def run_debugger_agent(progress=None, stream_callback=None):
    """
    Execute the full agentic debugging loop.

    Args:
        progress: optional callable(step: str, detail: str) called at each phase.

    Returns a dict with keys:
        status        "success" | "partial" | "error"
        iterations    int
        bug_analysis  str
        fixed_code    str
        test_output   str
        error         str | None
    """

    def _update(step: str, detail: str = ""):
        logger.info("%s: %s", step, detail)
        if progress:
            progress(step, detail)

    try:
        client: ollama.Client = _get_client()

        # ── Phase 1: Observe ───────────────────────────────────────────────────
        _update("OBSERVE", f"Reading {BROKEN_LOGIC_PATH.name}")
        broken_code = BROKEN_LOGIC_PATH.read_text(encoding="utf-8")

        # ── Phase 2: Plan ──────────────────────────────────────────────────────
        _update("PLAN", f"Asking {OLLAMA_MODEL} to identify bugs…")
        bug_analysis = _analyze_bugs(client, broken_code, token_cb=stream_callback)
        _update("PLAN_DONE", bug_analysis)

        test_error: str | None = None
        fixed_code = ""

        for iteration in range(1, MAX_ITERATIONS + 1):
            # ── Phase 3: Fix ───────────────────────────────────────────────────
            _update("FIX", f"Generating fix (attempt {iteration}/{MAX_ITERATIONS})…")
            fixed_code = _generate_fix(client, broken_code, bug_analysis, test_error, token_cb=stream_callback)
            TARGET_PATH.write_text(fixed_code, encoding="utf-8")
            _update("WRITE", f"Wrote fix to {TARGET_PATH.name}")

            # ── Phase 4: Test ──────────────────────────────────────────────────
            _update("TEST", "Running pytest…")
            passed, test_output = _run_pytest()

            # ── Phase 5: Evaluate ──────────────────────────────────────────────
            if passed:
                _update("SUCCESS", f"All tests passed on attempt {iteration}")
                return {
                    "status": "success",
                    "iterations": iteration,
                    "bug_analysis": bug_analysis,
                    "fixed_code": fixed_code,
                    "test_output": test_output,
                    "error": None,
                }

            _update("RETRY", f"Tests failed on attempt {iteration}, retrying…")
            test_error = test_output

        _update("PARTIAL", f"Stopped after {MAX_ITERATIONS} attempts")
        return {
            "status": "partial",
            "iterations": MAX_ITERATIONS,
            "bug_analysis": bug_analysis,
            "fixed_code": fixed_code,
            "test_output": test_error or "",
            "error": None,
        }

    except Exception as exc:
        logger.exception("Agent crashed: %s", exc)
        return {
            "status": "error",
            "iterations": 0,
            "bug_analysis": "",
            "fixed_code": "",
            "test_output": "",
            "error": str(exc),
        }


def reset_to_broken():
    """Restore logic_utils.py to the broken state for a fresh demo run."""
    broken = BROKEN_LOGIC_PATH.read_text(encoding="utf-8")
    TARGET_PATH.write_text(broken, encoding="utf-8")
    logger.info("Reset logic_utils.py to broken state")
