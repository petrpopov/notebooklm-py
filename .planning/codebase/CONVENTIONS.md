# Coding Conventions

**Analysis Date:** 2026-03-15

## Naming Patterns

**Files:**
- Lowercase with underscores for modules: `_notebooks.py`, `_sources.py`, `_chat.py`
- Entry points are descriptive: `client.py`, `auth.py`, `exceptions.py`
- CLI commands use kebab-case in names: `notebooklm_cli.py`, but internal imports use underscores
- Test files follow pattern: `test_*.py` for unit tests, with corresponding module name

**Functions:**
- Async functions use lowercase with underscores: `async def list()`, `async def ask()`
- Private methods/functions prefix with underscore: `_build_url()`, `_try_refresh_and_retry()`
- Helper functions in cli: `with_client`, `resolve_notebook_id`, `require_notebook`
- Factory functions: `from_storage()`, `from_api_response()`

**Variables:**
- Snake_case for all variables: `notebook_id`, `csrf_token`, `source_ids`, `conversation_id`
- Constants in UPPER_CASE: `DEFAULT_TIMEOUT`, `MAX_CONVERSATION_CACHE_SIZE`, `AUTH_ERROR_PATTERNS`
- Private module-level variables: `_DEFAULT_BL`, `_UUID_PATTERN`, `_refresh_lock`
- Class attributes use underscore prefix for private: `self._core`, `self._http_client`

**Types:**
- Classes use PascalCase: `NotebookLMClient`, `ClientCore`, `NotebooksAPI`, `AuthTokens`
- Dataclasses for data models: `Notebook`, `Source`, `Artifact`, `AskResult`
- Enums use PascalCase: `SourceType`, `ArtifactType`, `ChatGoal`, `RPCMethod`
- Type unions use pipe syntax (Python 3.10+): `str | None`, `list[str] | None`, `dict[str, str]`

## Code Style

**Formatting:**
- Tool: Ruff formatter
- Line length: 100 characters (configured in `pyproject.toml`)
- Quote style: Double quotes (`"`)
- Indent: 4 spaces

**Linting:**
- Tool: Ruff with custom rules
- Selected rules: E, W, F, I, B, C4, UP, SIM (see `pyproject.toml` for full config)
- Ignored rules: E501 (long lines handled by formatter), B008 (Click uses function calls in defaults), SIM102, SIM105
- Per-file ignores: `src/notebooklm/__init__.py` and `src/notebooklm/notebooklm_cli.py` ignore E402 (module level imports not at top)

**Type Checking:**
- Tool: mypy
- Python version: 3.10+
- Strict optional checking in CLI modules
- Backward compatibility aliases for deprecated attributes (see `exceptions.py` for pattern)

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports (httpx, click, rich)
3. Local imports (from . or from ..)

**Path Aliases:**
- Known first-party: `notebooklm` (configured in `[tool.ruff.lint.isort]`)
- No complex path aliases; imports are relative within package
- TYPE_CHECKING blocks for forward references: `if TYPE_CHECKING: from ._sources import SourcesAPI`

**Example:**
```python
import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
from rich.table import Table

from ._core import ClientCore
from .rpc import RPCMethod
from .types import Notebook

if TYPE_CHECKING:
    from ._sources import SourcesAPI

logger = logging.getLogger(__name__)
```

## Error Handling

**Pattern:**
- All exceptions inherit from `NotebookLMError` base class
- Domain-specific exceptions: `SourceError`, `ArtifactError`, `ChatError`, etc.
- RPC-specific errors: `RPCError`, `AuthError`, `RateLimitError`, `ServerError`, `ClientError`
- Custom `__init__` methods with keyword-only arguments for context: `message`, `method_id`, `original_error`, etc.

**Usage:**
```python
# Raise with context
raise SourceAddError(
    url,
    cause=original_exception,
    message="Custom error message"
)

# Catch all library errors
try:
    await client.notebooks.list()
except NotebookLMError as e:
    handle_error(e)

# Catch specific errors
except SourceTimeoutError as e:
    # Access attributes like e.source_id, e.timeout, e.last_status
    pass
```

**Error Detection Functions:**
- Use `is_auth_error(exception)` to classify auth failures reliably
- Include helper functions for error classification at module level: `is_auth_error()` in `_core.py`

## Logging

**Framework:** Python standard `logging`

**Pattern:**
- Get logger at module level: `logger = logging.getLogger(__name__)`
- Use lazy interpolation with `%` operator: `logger.debug("Message: %s", variable)`
- Log levels: `debug` for flow/decisions, `warning` for unexpected but handled conditions
- No logging at INFO or ERROR levels for normal operation (use exceptions for errors)

**Examples:**
```python
logger.debug("Listing notebooks")
logger.debug("Creating notebook: %s", title)
logger.debug("Created notebook: %s", notebook.id)
logger.debug("Encoding RPC: method=%s, param_count=%d", method.value, len(params))
logger.warning("Detected auth error, will retry: %s", error)
```

**CLI Logging:**
- Disable ANSI color/formatting in tests: Set `NO_COLOR=1` and `TERM=dumb` in test environment
- Use Rich library for formatted console output (tables, panels, etc.)

## Comments

**When to Comment:**
- Complex RPC parameter nesting (e.g., `[[[id]]]]` vs `[[id]]`): Always explain why
- Non-obvious workarounds for API quirks: Document the Google API behavior being worked around
- Comments should explain *why*, not *what* (code explains what)

**JSDoc/TSDoc:**
- Use triple-quoted docstrings for all public functions/classes/modules
- Include section headers: Args, Returns, Raises, Example
- Keep docstrings concise but complete

**Example:**
```python
async def ask(
    self,
    notebook_id: str,
    question: str,
    source_ids: list[str] | None = None,
    conversation_id: str | None = None,
) -> AskResult:
    """Ask the notebook a question.

    Args:
        notebook_id: The notebook ID.
        question: The question to ask.
        source_ids: Specific source IDs to query. If None, uses all sources.
        conversation_id: Existing conversation ID for follow-up questions.

    Returns:
        AskResult with answer, conversation_id, and turn info.

    Example:
        # New conversation
        result = await client.chat.ask(notebook_id, "What is machine learning?")

        # Follow-up
        result = await client.chat.ask(
            notebook_id,
            "How does it differ from deep learning?",
            conversation_id=result.conversation_id
        )
    """
```

## Function Design

**Size:** Keep functions focused on single responsibility; large APIs (`_chat.py` 793 lines, `_artifacts.py` 669 lines) group related methods in a class

**Parameters:**
- Use type hints for all parameters and return values
- Async functions: Use `async def` consistently
- Keyword-only arguments (with `*`) for optional parameters: `def __init__(self, ..., *, method_id=None, original_error=None)`
- Default to `None` for optional parameters, use sentinel values only when `None` is meaningful

**Return Values:**
- Always specify return type: `-> list[Notebook]`, `-> None`, `-> AskResult | None`
- Async functions return coroutines: `async def list() -> list[Notebook]`
- Use dataclasses (`@dataclass`) for structured returns instead of dicts

## Module Design

**Exports:**
- Re-export key types in `__init__.py` for convenience: `from .types import Notebook, Source, ...`
- Mark backward compatibility aliases with deprecation warnings: See `exceptions.py` for `@property` aliases
- Minimize what's exported; focus on user-facing APIs

**Barrel Files:**
- Main `__init__.py` at `src/notebooklm/__init__.py` exports core client and exceptions
- CLI barrel `src/notebooklm/cli/__init__.py` imports and re-exports command groups from submodules
- RPC barrel `src/notebooklm/rpc/__init__.py` re-exports BATCHEXECUTE_URL, all errors, encoding/decoding functions

**Example Structure:**
```python
# src/notebooklm/__init__.py
from .client import NotebookLMClient
from .auth import AuthTokens
from .exceptions import NotebookLMError
from .types import Notebook, Source, Artifact

__all__ = ["NotebookLMClient", "AuthTokens", "NotebookLMError", "Notebook", "Source", "Artifact"]
```

## Async Pattern

- Use `async def` for all I/O-bound operations
- Context manager pattern: `async with NotebookLMClient.from_storage() as client:`
- Implement `__aenter__` and `__aexit__` for async context managers
- Use `asyncio.Lock()` for concurrent access control (see `_refresh_lock` in `_core.py`)
- No blocking calls in async functions; use `httpx.AsyncClient` for HTTP

## Data Structures

- Use `dataclasses` for type-safe data containers (not namedtuples or dicts)
- Use `OrderedDict` when insertion order matters (conversation cache in `_core.py`)
- Use `dict` for JSON-like responses from API; convert to dataclasses in parser code
- Use `list` for sequential data; avoid loose tuples in public APIs

---

*Convention analysis: 2026-03-15*
