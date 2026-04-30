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

# ── phase pipeline helpers ─────────────────────────────────────────────────────
_PHASE_ORDER = ["OBSERVE", "PLAN", "FIX", "TEST", "DONE"]
_PHASE_META = {
    "OBSERVE": ("🔍", "Observe"),
    "PLAN":    ("🧠", "Plan"),
    "FIX":     ("🔧", "Fix"),
    "TEST":    ("🧪", "Test"),
    "DONE":    ("✅", "Done"),
}
_STEP_TO_PHASE = {
    "OBSERVE": "OBSERVE", "PLAN": "PLAN", "PLAN_DONE": "PLAN",
    "FIX": "FIX", "WRITE": "FIX", "TEST": "TEST",
    "SUCCESS": "DONE", "RETRY": "TEST", "PARTIAL": "DONE",
}
_COMPLETES_PHASE = {"PLAN_DONE", "WRITE", "SUCCESS", "PARTIAL"}


def _phase_bar_html(active: str, done: set) -> str:
    parts = []
    for key in _PHASE_ORDER:
        icon, label = _PHASE_META[key]
        if key in done:
            bg, fg = "#28a745", "white"
        elif key == active:
            bg, fg = "#0d6efd", "white"
        else:
            bg, fg = "#3a3a4a", "#adb5bd"
        parts.append(
            f'<span style="background:{bg};color:{fg};padding:6px 16px;'
            f'border-radius:20px;font-weight:600;font-size:0.85rem">'
            f'{icon} {label}</span>'
        )
    return (
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0">'
        + "".join(parts) + "</div>"
    )


# ── agent run ──────────────────────────────────────────────────────────────────
with run_tab:
    start = st.button("▶ Start AI Debugger", type="primary")

    if start:
        step_log: list[tuple[str, str]] = []
        state = {"active_phase": "OBSERVE", "done_phases": set()}

        phase_bar = st.empty()
        phase_bar.markdown(_phase_bar_html(state["active_phase"], state["done_phases"]), unsafe_allow_html=True)

        st.caption("💬 Live agent output")
        stream_box = st.empty()

        st.divider()
        st.caption("📋 Phase log")
        log_placeholder = st.empty()

        phase_icons = {
            "OBSERVE": "🔍", "PLAN": "🧠", "PLAN_DONE": "📋",
            "FIX": "🔧", "WRITE": "💾", "TEST": "🧪",
            "SUCCESS": "✅", "RETRY": "🔁", "PARTIAL": "⚠️",
        }

        def progress(step: str, detail: str):
            step_log.append((step, detail))
            mapped = _STEP_TO_PHASE.get(step, state["active_phase"])
            state["active_phase"] = mapped
            if step in _COMPLETES_PHASE:
                state["done_phases"].add(mapped)
            if step in ("PLAN", "FIX"):
                stream_box.empty()
            phase_bar.markdown(_phase_bar_html(state["active_phase"], state["done_phases"]), unsafe_allow_html=True)
            lines = []
            for s, d in step_log:
                icon = phase_icons.get(s, "•")
                if s == "PLAN_DONE":
                    lines.append(f"{icon} **{s}** — *(analysis captured below)*")
                else:
                    short = d[:120] + "…" if len(d) > 120 else d
                    lines.append(f"{icon} **{s}** — {short}")
            log_placeholder.markdown("\n\n".join(lines))

        def stream_callback(text: str):
            tail = text[-600:] if len(text) > 600 else text
            stream_box.markdown(
                f'<div style="background:#1e1e2e;color:#cdd6f4;padding:12px 16px;'
                f'border-radius:8px;font-family:monospace;font-size:0.78rem;'
                f'max-height:220px;overflow-y:auto;white-space:pre-wrap;'
                f'border:1px solid #313244">{tail}</div>',
                unsafe_allow_html=True,
            )

        with st.spinner("Agent running…"):
            result = run_debugger_agent(progress=progress, stream_callback=stream_callback)

        stream_box.empty()
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
