ANALYZE_SYSTEM = (
    "You are a Python debugging expert. "
    "Identify bugs precisely: state the function name, what is wrong, and what the correct behavior should be."
)

ANALYZE_USER = """\
Analyze the following Python module for a number guessing game and list every bug you find.

For each bug include:
- Function name and approximate line
- What the code does wrong
- What it should do instead

```python
{code}
```"""

FIX_SYSTEM = (
    "You are a Python expert. "
    "When asked to fix code, return ONLY the corrected Python source. "
    "No markdown fences, no explanation, no commentary — raw Python only."
)

FIX_USER = """\
Fix the following broken Python module.

BROKEN CODE:
{broken_code}

BUGS IDENTIFIED:
{bug_analysis}

{error_section}\
Return the complete fixed Python file. Raw Python only."""

ERROR_SECTION = """\
A previous fix attempt failed with these pytest errors:
{test_error}

Study the failures and generate a better fix.

"""
