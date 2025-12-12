---
description: 'Python coding conventions and guidelines'
applyTo: '**/*.py'
---

# Python Execution and Package Management Instructions

## ⚠️ CRITICAL: UV-ONLY Policy
**NEVER use `python`, `pip`, or `venv` commands directly. ALWAYS use `uv` equivalents.**

## Quick Command Reference

### Running Code (NEVER use `python` directly)
-   ❌ `python script.py` → ✅ `uv run script.py`
-   ❌ `python -m module` → ✅ `uv run python -m module`
-   ❌ `python -c "code"` → ✅ `uv run python -c "code"`
-   ❌ Interactive: `python` → ✅ `uv run python`

### Package Management (NEVER use `pip` directly)
-   ❌ `pip install package` → ✅ `uv add package`
-   ❌ `pip install -r requirements.txt` → ✅ `uv sync` (preferred) or `uv pip install -r requirements.txt`
-   ❌ `pip uninstall package` → ✅ `uv remove package`
-   ❌ `pip list` → ✅ `uv pip list`
-   ❌ `pip freeze` → ✅ `uv pip freeze`

### Testing (NEVER activate venv or use python directly)
-   ❌ `python -m pytest` → ✅ `uv run pytest`
-   ❌ `pytest tests/` → ✅ `uv run pytest tests/`
-   ❌ `.venv/Scripts/activate && pytest` → ✅ `uv run pytest`

### Project Management
-   **Initialize project**: `uv init`
-   **Sync dependencies**: `uv sync` (installs from pyproject.toml/uv.lock)
-   **Update lock file**: `uv lock --upgrade`
-   **Add dev dependency**: `uv add --dev package`

### Environment Management (NEVER use `venv` directly)
-   ❌ `python -m venv .venv` → ✅ `uv venv`
-   ❌ `source .venv/bin/activate` → ✅ Not needed! Use `uv run` instead
-   **DO NOT manually activate virtual environments** - `uv run` handles this automatically

## Why UV?
-   **10-100x faster** than pip
-   **Automatic dependency resolution** without conflicts
-   **Built-in project management** with pyproject.toml
-   **No manual venv activation** needed

## When In Doubt
-   Prefix ANY Python command with `uv run`
-   For package operations, use `uv add`/`uv remove`
-   See `uv-python-usage-guide.instructions.md` for comprehensive documentation

## Common Mistakes to Avoid
1. ❌ Running raw `python` or `pytest` commands
2. ❌ Using `pip install` for adding dependencies
3. ❌ Manually activating virtual environments
4. ❌ Using `requirements.txt` instead of `pyproject.toml` + `uv.lock`
5. ❌ Forgetting `uv run` prefix for scripts

# Python Coding Conventions

## Python Instructions

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Provide docstrings following PEP 257 conventions.
- Use the `typing` module for type annotations (e.g., `List[str]`, `Dict[str, int]`).
- Break down complex functions into smaller, more manageable functions.

## General Instructions

- Always prioritize readability and clarity.
- For algorithm-related code, include explanations of the approach used.
- Write code with good maintainability practices, including comments on why certain design decisions were made.
- Handle edge cases and write clear exception handling.
- For libraries or external dependencies, mention their usage and purpose in comments.
- Use consistent naming conventions and follow language-specific best practices.
- Write concise, efficient, and idiomatic code that is also easily understandable.

## Code Style and Formatting

- Follow the **PEP 8** style guide for Python.
- Maintain proper indentation (use 4 spaces for each level of indentation).
- Ensure lines do not exceed 79 characters.
- Place function and class docstrings immediately after the `def` or `class` keyword.
- Use blank lines to separate functions, classes, and code blocks where appropriate.

## Edge Cases and Testing

- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and large datasets.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.

## Example of Proper Documentation

```python
def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.
    
    Parameters:
    radius (float): The radius of the circle.
    
    Returns:
    float: The area of the circle, calculated as π * radius^2.
    """
    import math
    return math.pi * radius ** 2
```
