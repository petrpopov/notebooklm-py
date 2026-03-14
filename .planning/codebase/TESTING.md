# Testing

## Framework & Configuration

- **Framework**: pytest with pytest-asyncio (asyncio_mode = "auto")
- **HTTP mocking**: pytest-httpx for integration tests
- **VCR cassettes**: vcrpy for recorded HTTP interactions
- **Coverage**: pytest-cov, enforced at 90% (`fail_under = 90`)
- **Timeout**: 60s global timeout (pytest-timeout), individual tests can override
- **Flaky tests**: pytest-rerunfailures available

### pytest.ini_options (pyproject.toml)
```toml
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
addopts = "--ignore=tests/e2e"  # e2e excluded by default
timeout = 60
markers = [
    "e2e: end-to-end tests requiring authentication",
    "variants: parameter variant tests (skip to save quota)",
    "readonly: read-only tests against user's test notebook",
    "vcr: tests using VCR.py recorded cassettes",
]
```

## Test Directory Structure

```
tests/
├── conftest.py              # Root-level shared fixtures
├── vcr_config.py            # VCR.py configuration (cassette dir, filter patterns)
├── unit/                    # Fast tests, no network
│   ├── cli/
│   │   ├── conftest.py      # CLI test fixtures (CliRunner, mock client)
│   │   └── test_*.py        # One per CLI module (test_notebook.py, test_source.py, etc.)
│   └── test_*.py            # One per source module (test_decoder.py, test_encoder.py, etc.)
├── integration/             # Mock HTTP with pytest-httpx or VCR
│   ├── conftest.py          # Integration fixtures
│   ├── cli_vcr/             # CLI tests with VCR cassettes
│   │   ├── conftest.py
│   │   └── test_*.py
│   └── test_*.py            # API integration tests
├── e2e/                     # Real API, require auth
│   ├── conftest.py          # Auth setup, real client fixture
│   └── test_*.py            # Full workflow tests
└── cassettes/               # VCR recorded YAML cassettes (~75 files)
```

## Test Types

### Unit Tests (`tests/unit/`)
- Test encoding/decoding, data parsing, utilities with no network
- CLI tests use Click's `CliRunner` with mocked client
- No HTTP requests allowed
- Examples: `test_encoder.py`, `test_decoder.py`, `test_auth.py`

### Integration Tests (`tests/integration/`)
- Use `pytest-httpx` to mock HTTP responses at the `httpx` level
- Or use VCR cassettes to replay recorded HTTP interactions
- Test full request/response cycles without real auth
- Examples: `test_notebooks.py`, `test_sources.py`, `test_chat.py`

### VCR CLI Tests (`tests/integration/cli_vcr/`)
- CLI commands tested with real recorded cassettes
- Record: `NOTEBOOKLM_VCR_RECORD=1 pytest tests/integration/cli_vcr/`
- Replay: standard `pytest` run uses cassettes automatically
- Marker: `@pytest.mark.vcr`

### E2E Tests (`tests/e2e/`)
- Require real auth (`notebooklm login` first, or env vars)
- Excluded from default run: `pytest tests/e2e -m e2e`
- Marker: `@pytest.mark.e2e`
- Some tests are `@pytest.mark.readonly` (safe against real data)

## Fixtures

### Root conftest (`tests/conftest.py`)
- Shared fixtures for auth tokens, mock HTTP responses

### CLI conftest (`tests/unit/cli/conftest.py`)
```python
@pytest.fixture
def cli_runner():
    return CliRunner()

@pytest.fixture
def mock_client():
    # AsyncMock of NotebookLMClient with namespaced API mocks
    client = AsyncMock(spec=NotebookLMClient)
    client.notebooks = AsyncMock()
    client.sources = AsyncMock()
    # ...
    return client
```

### Integration conftest (`tests/integration/conftest.py`)
- `httpx_mock` fixture (from pytest-httpx)
- Pre-configured mock response builders

## Mocking Patterns

### Mock client for CLI tests
```python
@patch("notebooklm.cli.notebook.create_client")
async def test_create(mock_create, cli_runner):
    mock_client = AsyncMock()
    mock_create.return_value.__aenter__.return_value = mock_client
    mock_client.notebooks.create.return_value = Notebook(id="nb1", ...)
    result = cli_runner.invoke(cli, ["create", "--title", "Test"])
    assert result.exit_code == 0
```

### HTTP mocking with pytest-httpx
```python
async def test_list_notebooks(httpx_mock):
    httpx_mock.add_response(
        url="https://notebooklm.google.com/...",
        json={...},
    )
    async with await NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
    assert len(notebooks) > 0
```

### VCR cassettes
```python
@pytest.mark.vcr
async def test_something():
    # Replays from tests/cassettes/test_something.yaml
    ...
```

## Coverage Requirements

- **Minimum**: 90% branch coverage (`fail_under = 90`)
- **Source**: `src/notebooklm` only
- **Run**: `pytest --cov` or `pytest --cov --cov-report=html`
- **Config**: `[tool.coverage.run]` / `[tool.coverage.report]` in pyproject.toml
- Branch coverage enabled (`branch = true`)
- Shows missing lines in report

## Running Tests

```bash
# All non-e2e tests
pytest

# With coverage
pytest --cov

# Specific test file
pytest tests/unit/test_decoder.py

# E2E tests (requires auth)
pytest tests/e2e -m e2e

# VCR tests only
pytest -m vcr

# Record new VCR cassettes
NOTEBOOKLM_VCR_RECORD=1 pytest tests/integration/cli_vcr/

# Skip variant tests (saves quota)
pytest -m "not variants"
```

## Test Naming Patterns

- Test files: `test_<module_name>.py` (mirrors source file names)
- Test functions: `test_<action>_<scenario>` (e.g., `test_create_notebook_success`)
- Test classes: `Test<FeatureName>` when grouping related tests
- Async tests: `async def test_*` (auto-detected by asyncio_mode = "auto")

## What NOT to Mock

- **RPC encoding/decoding**: Test with real data structures, not mocks
- **Data parsing in decoder.py**: Test with actual captured response fixtures
- **Exception types**: Test real exception hierarchy, not generic exceptions
