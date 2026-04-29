"""
Unit tests for agent helper functions.

These test the reliability guards inside the agent itself — specifically the
fence-stripping logic that handles LLM output cleanup, which is a real failure
mode: local models often wrap output in ```python fences despite instructions
not to.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.debugger_agent import _strip_fences


def test_strip_fences_removes_python_fence():
    code = "```python\ndef foo():\n    return 1\n```"
    result = _strip_fences(code)
    assert result == "def foo():\n    return 1"
    assert "```" not in result


def test_strip_fences_removes_plain_fence():
    code = "```\ndef foo():\n    return 1\n```"
    result = _strip_fences(code)
    assert result == "def foo():\n    return 1"
    assert "```" not in result


def test_strip_fences_no_fence_unchanged():
    code = "def foo():\n    return 1"
    assert _strip_fences(code) == code


def test_strip_fences_no_closing_fence():
    # Some models omit the closing fence — inner lines should still be returned
    code = "```python\ndef foo():\n    return 1"
    result = _strip_fences(code)
    assert "def foo():" in result
    assert "```" not in result


def test_strip_fences_strips_surrounding_whitespace():
    code = "\n\n```python\ndef foo():\n    return 1\n```\n\n"
    result = _strip_fences(code)
    assert result == "def foo():\n    return 1"


def test_strip_fences_multifunction_file():
    # Realistic case: full module wrapped in fences
    code = (
        "```python\n"
        "def check_guess(guess, secret):\n"
        "    if guess == secret:\n"
        "        return 'Win', 'Correct!'\n"
        "    if guess > secret:\n"
        "        return 'Too High', 'Go LOWER!'\n"
        "    return 'Too Low', 'Go HIGHER!'\n"
        "```"
    )
    result = _strip_fences(code)
    assert result.startswith("def check_guess")
    assert "```" not in result
