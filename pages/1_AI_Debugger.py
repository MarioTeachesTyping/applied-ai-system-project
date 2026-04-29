"""
AI Debugger page — shows the agentic loop running live in the browser.
"""

import difflib
from pathlib import Path

import streamlit as st

from agent.debugger_agent import (
    BROKEN_LOGIC_PATH,
    TARGET_PATH,
    run_debugger_agent,
    reset_to_broken,
)

st.set_page_config(page_title="AI Debugger", page_icon="🤖", layout="wide")

st.title("🤖 AI Debugging Agent")
st.caption(
    "The agent reads broken code, identifies bugs, generates a fix, "
    "runs pytest, and iterates until all tests pass."
)

# ── sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Reset to broken state", help="Overwrites logic_utils.py with the buggy version so you can re-run the demo"):
        reset_to_broken()
        st.success("logic_utils.py reset to broken state.")

    st.divider()
    st.markdown(
        "**How it works**\n\n"
        "1. **Observe** — read `broken_game/broken_logic.py`\n"
        "2. **Plan** — LLM identifies bugs\n"
        "3. **Fix** — LLM generates corrected code\n"
        "4. **Test** — `pytest` runs as oracle\n"
        "5. **Evaluate** — pass → done, fail → retry (max 3×)\n"
    )

# ── code preview tabs ──────────────────────────────────────────────────────────
broken_code = BROKEN_LOGIC_PATH.read_text(encoding="utf-8")

preview_tab, run_tab = st.tabs(["🔴 Broken Code", "▶ Run Agent"])

with preview_tab:
    st.caption(f"`{BROKEN_LOGIC_PATH}`  —  intentionally broken artifact")
    st.code(broken_code, language="python")

# ── agent run ──────────────────────────────────────────────────────────────────
with run_tab:
    start = st.button("▶ Start AI Debugger", type="primary")

    if start:
        # Accumulate step messages so the log survives widget rerenders
        step_log: list[tuple[str, str]] = []

        phase_icons = {
            "OBSERVE": "🔍",
            "PLAN": "🧠",
            "PLAN_DONE": "📋",
            "FIX": "🔧",
            "WRITE": "💾",
            "TEST": "🧪",
            "SUCCESS": "✅",
            "RETRY": "🔁",
            "PARTIAL": "⚠️",
        }

        log_placeholder = st.empty()

        def progress(step: str, detail: str):
            step_log.append((step, detail))
            lines = []
            for s, d in step_log:
                icon = phase_icons.get(s, "•")
                # Don't repeat the full bug analysis inline — too long
                if s == "PLAN_DONE":
                    lines.append(f"{icon} **{s}** — *(analysis captured below)*")
                else:
                    short = d[:120] + "…" if len(d) > 120 else d
                    lines.append(f"{icon} **{s}** — {short}")
            log_placeholder.markdown("\n\n".join(lines))

        with st.spinner("Agent running…"):
            result = run_debugger_agent(progress=progress)

        st.divider()

        # ── result banner ──────────────────────────────────────────────────────
        if result["status"] == "success":
            st.success(
                f"All tests passed — fixed in {result['iterations']} "
                f"iteration{'s' if result['iterations'] != 1 else ''}."
            )
        elif result["status"] == "partial":
            st.warning(
                f"Partial fix after {result['iterations']} iterations. "
                "Some tests may still fail."
            )
        else:
            st.error(f"Agent error: {result['error']}")
            st.stop()

        # ── three result columns ───────────────────────────────────────────────
        col_bugs, col_diff, col_tests = st.columns([2, 2, 2])

        with col_bugs:
            st.subheader("Bug Analysis")
            st.markdown(result["bug_analysis"])

        with col_diff:
            st.subheader("Code Diff")
            fixed_code = result["fixed_code"]
            diff_lines = list(
                difflib.unified_diff(
                    broken_code.splitlines(keepends=True),
                    fixed_code.splitlines(keepends=True),
                    fromfile="broken_logic.py",
                    tofile="logic_utils.py (fixed)",
                    lineterm="",
                )
            )
            if diff_lines:
                st.code("".join(diff_lines), language="diff")
            else:
                st.info("No changes produced.")

        with col_tests:
            st.subheader("Test Output")
            st.code(result["test_output"], language="text")
