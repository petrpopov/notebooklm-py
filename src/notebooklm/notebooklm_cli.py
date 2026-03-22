"""CLI interface for NotebookLM automation.

Command structure:
  notebooklm login                    # Authenticate
  notebooklm use <notebook_id>        # Set current notebook context
  notebooklm status                   # Show current context
  notebooklm list                     # List notebooks
  notebooklm create <title>           # Create notebook
  notebooklm ask <question>           # Ask the current notebook a question

  notebooklm source <command>         # Source operations
  notebooklm artifact <command>       # Artifact management
  notebooklm generate <type>          # Generate content
  notebooklm download <type>          # Download content
  notebooklm note <command>           # Note operations
  notebooklm research <command>       # Research status/wait

LLM-friendly design:
  # Set context once, then use simple commands
  notebooklm use nb123
  notebooklm generate video "a funny explainer for kids"
  notebooklm generate audio "deep dive focusing on chapter 3"
  notebooklm ask "what are the key themes?"
"""

# Runtime Python version guard (must run before any PEP 604 syntax is evaluated)
import sys

from ._version_check import check_python_version as _check_python_version

_check_python_version()
del _check_python_version

import asyncio
import logging
import os
from pathlib import Path

# =============================================================================
# WINDOWS COMPATIBILITY FIXES (issue #75, #79, #80)
# Must be applied before any async code runs
# =============================================================================

if sys.platform == "win32":
    # Fix #79: Windows asyncio ProactorEventLoop can hang indefinitely at IOCP layer
    # (GetQueuedCompletionStatus) in certain environments like Sandboxie.
    # SelectorEventLoop avoids this issue.
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Fix #80: Non-English Windows systems (cp950, cp932, etc.) can fail with
    # UnicodeEncodeError when outputting Unicode characters like checkmarks.
    # Setting PYTHONUTF8 ensures consistent UTF-8 encoding.
    os.environ.setdefault("PYTHONUTF8", "1")

import click

from . import __version__
from .auth import DEFAULT_STORAGE_PATH

# Import command groups from cli package
from .cli import (
    agent,
    artifact,
    download,
    generate,
    language,
    note,
    register_chat_commands,
    register_notebook_commands,
    # Register functions for top-level commands
    register_session_commands,
    research,
    share,
    skill,
    source,
)
from .cli.grouped import SectionedGroup

# Import helpers needed for backward compatibility with tests


# =============================================================================
# MAIN CLI GROUP
# =============================================================================


@click.group(cls=SectionedGroup)
@click.version_option(version=__version__, prog_name="NotebookLM CLI")
@click.option(
    "--storage",
    type=click.Path(exists=False),
    default=None,
    help=f"Path to storage_state.json (default: {DEFAULT_STORAGE_PATH})",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v for INFO, -vv for DEBUG)",
)
@click.pass_context
def cli(ctx, storage, verbose):
    """NotebookLM CLI.

    \b
    Quick start:
      notebooklm login              # Authenticate first
      notebooklm list               # List your notebooks
      notebooklm create "My Notes"  # Create a notebook
      notebooklm ask "Hi"           # Ask the current notebook a question

    \b
    Tip: Use partial notebook IDs (e.g., 'notebooklm use abc' matches 'abc123...')
    """
    # Configure logging based on verbosity: -v for INFO, -vv+ for DEBUG
    if verbose >= 2:
        logging.getLogger("notebooklm").setLevel(logging.DEBUG)
    elif verbose == 1:
        logging.getLogger("notebooklm").setLevel(logging.INFO)

    ctx.ensure_object(dict)
    ctx.obj["storage_path"] = Path(storage) if storage else None


# =============================================================================
# REGISTER COMMANDS
# =============================================================================

# Register top-level commands from modules
register_session_commands(cli)
register_notebook_commands(cli)
register_chat_commands(cli)

# Register command groups (subcommand style)
cli.add_command(source)
cli.add_command(artifact)
cli.add_command(agent)
cli.add_command(generate)
cli.add_command(download)
cli.add_command(note)
cli.add_command(share)
cli.add_command(skill)
cli.add_command(research)
cli.add_command(language)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def _detect_macos_system_proxy():
    """Detect macOS system proxy via scutil and set env vars for httpx.

    Only sets env vars that are not already defined, so explicit user
    configuration always takes precedence.
    """
    if sys.platform != "darwin":
        return

    import subprocess

    try:
        result = subprocess.run(
            ["scutil", "--proxy"], capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return

        output = result.stdout
        # Parse SOCKS proxy
        if "SOCKSEnable : 1" in output:
            host, port = None, None
            for line in output.splitlines():
                if "SOCKSProxy :" in line:
                    host = line.split(":")[-1].strip()
                elif "SOCKSPort :" in line:
                    port = line.split(":")[-1].strip()
            if host and port:
                os.environ.setdefault("ALL_PROXY", f"socks5://{host}:{port}")

        # Parse HTTP proxy
        if "HTTPEnable : 1" in output:
            host, port = None, None
            for line in output.splitlines():
                if "HTTPProxy :" in line:
                    host = line.split(":")[-1].strip()
                elif "HTTPPort :" in line:
                    port = line.split(":")[-1].strip()
            if host and port:
                os.environ.setdefault("HTTP_PROXY", f"http://{host}:{port}")
                os.environ.setdefault("http_proxy", f"http://{host}:{port}")

        # Parse HTTPS proxy
        if "HTTPSEnable : 1" in output:
            host, port = None, None
            for line in output.splitlines():
                if "HTTPSProxy :" in line:
                    host = line.split(":")[-1].strip()
                elif "HTTPSPort :" in line:
                    port = line.split(":")[-1].strip()
            if host and port:
                os.environ.setdefault("HTTPS_PROXY", f"https://{host}:{port}")
                os.environ.setdefault("https_proxy", f"https://{host}:{port}")

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass


def main():
    # Detect macOS system proxy and set env vars for httpx
    _detect_macos_system_proxy()

    # Windows-specific fixes
    if sys.platform == "win32":
        # Force UTF-8 encoding for Unicode output on non-English Windows systems
        # Prevents UnicodeEncodeError when displaying Unicode characters (✓, ✗, box drawing)
        # on systems with legacy encodings (cp950, cp932, cp936, etc.)
        os.environ.setdefault("PYTHONUTF8", "1")

        # Fix asyncio hanging issue - use WindowsSelectorEventLoopPolicy instead of
        # default ProactorEventLoop to avoid IOCP blocking on network operations
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    cli()


if __name__ == "__main__":
    main()
