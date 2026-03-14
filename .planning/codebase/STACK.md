# Technology Stack

**Analysis Date:** 2026-03-15

## Languages

**Primary:**
- Python 3.10+ - Core library and CLI application
- Supports Python 3.10, 3.11, 3.12, 3.13, 3.14 per `pyproject.toml`

## Runtime

**Environment:**
- Python 3.10 minimum required version (specified in `pyproject.toml`)
- Async-first: Uses `asyncio` for all network I/O
- Context manager patterns for resource lifecycle management

**Package Manager:**
- pip (via pyproject.toml)
- uv recommended for faster installs and venv management (documented in CLAUDE.md)
- Lockfile: Not detected (pip dependencies only)

## Frameworks

**Core:**
- Click 8.0+ - CLI framework for command parsing and routing (`src/notebooklm/cli/`)
- No web framework (library-only, CLI as interface layer)

**HTTP/Network:**
- httpx 0.27.0+ - Async HTTP client for all API calls
  - Used in `src/notebooklm/_core.py` for RPC calls
  - Used in `src/notebooklm/auth.py` for token fetching
  - Used in `src/notebooklm/_chat.py` for streaming query endpoint
  - Used in artifact download operations
  - Configured with granular timeouts (connect: 10s, read/write: 30s default)

**Browser Automation (optional):**
- Playwright 1.40.0+ - Browser automation for login flow
  - Optional dependency: `pip install notebooklm[browser]`
  - Supports Chromium (default) and Microsoft Edge (launch_kwargs: channel="msedge")
  - Used in `src/notebooklm/cli/session.py` for Google authentication
  - Saves Playwright storage_state.json to `~/.notebooklm/storage_state.json`
  - Persistent browser profile stored in `~/.notebooklm/browser-profile/`
  - Windows support: Uses ProactorEventLoop for Playwright, WindowsSelectorEventLoopPolicy for other async ops

**UI/Output:**
- Rich 13.0+ - Terminal table formatting and colored output
  - Used in `src/notebooklm/cli/` for formatted command output
  - Table rendering, progress indicators, colored text

**Testing:**
- pytest 8.0.0+ - Test runner
- pytest-asyncio 0.23.0+ - Async test support
- pytest-httpx 0.30.0+ - HTTP mocking for tests
- pytest-cov 4.0.0+ - Coverage reporting (minimum 90% threshold per config)
- pytest-rerunfailures 14.0+ - Flaky test rerun support
- pytest-timeout 2.3.0+ - Global 60s test timeout (configurable per-test)
- vcrpy 6.0.0+ - Recorded HTTP cassettes for VCR tests

**Code Quality:**
- mypy 1.0.0+ - Static type checking
  - Config: `pyproject.toml` [tool.mypy]
  - Target: Python 3.10
  - check_untyped_defs: true (but disallow_untyped_defs: false for pragmatism)
- ruff 0.4.0+ - Linting and formatting
  - Integrated formatter and linter (replaces black, isort, flake8, pyupgrade)
  - Line length: 100 characters
  - Rulesets: E/W (pycodestyle), F (pyflakes), I (isort), B (bugbear), C4 (comprehensions), UP (pyupgrade), SIM (simplify)
  - Excludes: E501 (line length, handled by formatter), B008 (Click default args), SIM102/105 (readability)
  - Quote style: double quotes
  - Indent: spaces

**Configuration:**
- python-dotenv 1.0.0+ - Environment variable loading (.env support)
- pre-commit 4.5.1+ - Git pre-commit hooks framework

## Key Dependencies

**Critical (Core API):**
- httpx 0.27.0+ - HTTP client for all batchexecute RPC calls and streaming queries
  - Cookies and auth headers managed in `src/notebooklm/_core.py`
  - Timeouts configured per request type
  - Error handling for 429 (rate limit), 5xx (server), 4xx (client), network errors

**Infrastructure:**
- Click 8.0.0+ - CLI command routing and argument parsing
- Rich 13.0.0+ - Terminal formatting
- Playwright 1.40.0+ (optional) - Browser automation for authentication
- python-dotenv 1.0.0+ - Environment variable support (CI/CD friendly)

## Configuration

**Environment:**
- NOTEBOOKLM_HOME - Override default config directory (defaults to ~/.notebooklm)
- NOTEBOOKLM_AUTH_JSON - Inline Playwright storage_state JSON for CI/CD (no file writes)
- NOTEBOOKLM_VCR_RECORD - Enable VCR cassette recording for test development
- NOTEBOOKLM_BL - Override browser loader version string (advanced debugging)
- Python env vars: Loaded via python-dotenv

**Build:**
- Hatchling - Build backend
- hatch-fancy-pypi-readme - README handling for PyPI

**Project Config Files:**
- `pyproject.toml` - Package metadata, dependencies, tool configurations
- `.python-version` - Not detected (uses requires-python in pyproject.toml)
- No setup.py or setup.cfg (modern pyproject.toml only)

## Platform Requirements

**Development:**
- Python 3.10+
- uv (recommended) or pip
- playwright (optional, for login feature)
- Git (for pre-commit hooks)

**Windows-specific:**
- ProactorEventLoop policy handling for Playwright subprocess compatibility
- Microsoft Edge support as alternative to Chromium

**Production:**
- Python 3.10+ runtime
- httpx (core dependency) - works on all platforms
- Playwright optional for browser-based auth or if using CLI
- No external services required (uses Google's internal APIs)

---

*Stack analysis: 2026-03-15*
