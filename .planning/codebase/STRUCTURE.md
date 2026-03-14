# Codebase Structure

## Directory Layout

```
notebooklm-py/
├── src/notebooklm/          # Main package source
│   ├── __init__.py          # Public API exports
│   ├── __main__.py          # python -m notebooklm entry point
│   ├── client.py            # NotebookLMClient (main entry point)
│   ├── auth.py              # Authentication handling
│   ├── types.py             # Public dataclasses and type definitions
│   ├── exceptions.py        # Exception hierarchy
│   ├── paths.py             # Storage path management
│   ├── notebooklm_cli.py    # CLI entry point (main())
│   ├── _core.py             # HTTP client + RPC infrastructure
│   ├── _notebooks.py        # NotebooksAPI domain implementation
│   ├── _sources.py          # SourcesAPI domain implementation
│   ├── _artifacts.py        # ArtifactsAPI domain implementation
│   ├── _chat.py             # ChatAPI domain implementation
│   ├── _research.py         # ResearchAPI domain implementation
│   ├── _notes.py            # NotesAPI domain implementation
│   ├── _settings.py         # SettingsAPI domain implementation
│   ├── _sharing.py          # SharingAPI domain implementation
│   ├── _logging.py          # Logging configuration
│   ├── _url_utils.py        # URL parsing utilities
│   ├── _version_check.py    # Version check on startup
│   ├── rpc/                 # RPC protocol layer
│   │   ├── __init__.py
│   │   ├── types.py         # RPC method IDs and enums (source of truth)
│   │   ├── encoder.py       # Request encoding to batchexecute format
│   │   └── decoder.py       # Response parsing from nested list structures
│   └── cli/                 # CLI command modules
│       ├── __init__.py
│       ├── helpers.py       # Shared CLI utilities (resolve notebook, etc.)
│       ├── options.py       # Shared Click options/decorators
│       ├── error_handler.py # CLI error display
│       ├── grouped.py       # Command group registration
│       ├── agent.py         # agent command
│       ├── agent_templates.py # SKILL.md/AGENTS.md templates
│       ├── artifact.py      # artifact subcommands
│       ├── chat.py          # ask, configure, history
│       ├── download.py      # download subcommands
│       ├── download_helpers.py # Download utilities
│       ├── generate.py      # generate audio, video, etc.
│       ├── language.py      # language selection
│       ├── note.py          # note subcommands
│       ├── notebook.py      # list, create, delete, rename
│       ├── research.py      # research subcommands
│       ├── session.py       # login, use, status, clear
│       ├── share.py         # share subcommands
│       ├── skill.py         # skill packaging commands
│       └── source.py        # source add, list, delete
├── tests/
│   ├── conftest.py          # Root fixtures
│   ├── vcr_config.py        # VCR.py configuration
│   ├── unit/                # Unit tests (no network)
│   │   ├── cli/             # CLI command unit tests
│   │   │   ├── conftest.py  # CLI test fixtures
│   │   │   └── test_*.py    # One file per CLI module
│   │   └── test_*.py        # One file per source module
│   ├── integration/         # Integration tests (mock HTTP)
│   │   ├── conftest.py      # Integration fixtures
│   │   ├── cli_vcr/         # CLI tests with VCR cassettes
│   │   │   ├── conftest.py
│   │   │   └── test_*.py
│   │   └── test_*.py        # API integration tests
│   ├── e2e/                 # E2E tests (real API, require auth)
│   │   ├── conftest.py
│   │   └── test_*.py
│   └── cassettes/           # VCR recorded HTTP cassettes (75 files)
├── docs/                    # Documentation
│   ├── cli-reference.md     # CLI command reference
│   ├── python-api.md        # Python API reference
│   ├── configuration.md     # Storage and settings
│   ├── troubleshooting.md   # Known issues
│   ├── development.md       # Architecture, testing, releasing
│   ├── rpc-development.md   # RPC capture and debugging
│   ├── rpc-reference.md     # RPC payload structures
│   ├── stability.md         # Stability guarantees
│   ├── releasing.md         # Release process
│   └── examples/            # Runnable example scripts
│       ├── quickstart.py
│       ├── chat.py
│       ├── bulk-import.py
│       ├── notes.py
│       ├── research-to-podcast.py
│       └── video.py
├── scripts/                 # Maintenance scripts
│   ├── check_rpc_health.py  # Verify RPC method IDs still work
│   └── diagnose_get_notebook.py # Debug notebook fetch
├── .github/workflows/       # CI/CD pipelines
│   ├── test.yml             # Main test suite
│   ├── nightly.yml          # Nightly e2e runs
│   ├── rpc-health.yml       # RPC health check
│   ├── publish.yml          # PyPI publishing
│   ├── codeql.yml           # Security scanning
│   └── verify-*.yml         # Package verification
├── .planning/codebase/      # Codebase map documents
├── pyproject.toml           # Project config, deps, tool config
├── CLAUDE.md                # Claude Code instructions
├── AGENTS.md                # AI agent usage guide
├── SKILL.md                 # NotebookLM skill definition
├── CONTRIBUTING.md          # Contribution guidelines
├── SECURITY.md              # Security policy
├── CHANGELOG.md             # Version history
└── README.md                # Project overview
```

## Key Locations

| Purpose | Location |
|---------|----------|
| Main client class | `src/notebooklm/client.py` |
| RPC method IDs | `src/notebooklm/rpc/types.py` |
| Public types/dataclasses | `src/notebooklm/types.py` |
| Public API exports | `src/notebooklm/__init__.py` |
| CLI entry point | `src/notebooklm/notebooklm_cli.py` |
| Auth tokens storage | `~/.notebooklm/` (via `paths.py`) |
| Test cassettes | `tests/cassettes/` |
| VCR config | `tests/vcr_config.py` |

## Naming Conventions

### Files
- `_*.py` prefix → internal/private domain APIs (e.g., `_notebooks.py`, `_sources.py`)
- `client.py` → main public client
- `types.py` → data model definitions
- `auth.py`, `paths.py`, `exceptions.py` → standalone utilities
- `rpc/` → all RPC protocol code isolated here
- `cli/` → all CLI command code isolated here
- `test_*.py` → all test files prefixed with `test_`

### Python
- Classes: `PascalCase` (e.g., `NotebookLMClient`, `NotebooksAPI`, `AuthTokens`)
- Functions/methods: `snake_case` (e.g., `get_notebook`, `add_url`)
- Private methods: `_snake_case` prefix
- Constants/enums: `UPPER_SNAKE_CASE` (e.g., `RpcMethod.NOTEBOOK_LIST`)
- Type aliases: `PascalCase` (e.g., `NotebookId`, `SourceId`)

### CLI Commands
- Top-level verbs: `login`, `use`, `status`, `clear`, `list`, `create`, `ask`
- Grouped commands: `source add`, `artifact list`, `generate audio`, `download video`, `note create`
- Options: `--kebab-case` (e.g., `--notebook-id`, `--output-file`)

## Adding New Code

### New RPC operation
1. Add method ID to `src/notebooklm/rpc/types.py`
2. Add encoder function in `src/notebooklm/rpc/encoder.py`
3. Add decoder function in `src/notebooklm/rpc/decoder.py`
4. Implement in appropriate `_*.py` domain file
5. Expose via `client.py` namespace attribute

### New domain API
1. Create `src/notebooklm/_domain.py`
2. Add `@property` to `NotebookLMClient` returning `DomainAPI(self._core)`
3. Export from `src/notebooklm/__init__.py`
4. Add CLI commands in `src/notebooklm/cli/domain.py`
5. Register in `src/notebooklm/cli/grouped.py`

### New CLI command
1. Add Click command to relevant `cli/*.py` module
2. Register in `cli/grouped.py` or `notebooklm_cli.py`
3. Add shared options to `cli/options.py`
4. Update `docs/cli-reference.md`
