"""Command-line interface for Legal support agents."""

from __future__ import annotations

import sys

from legal_support import __version__


def main() -> int:
    """Main entry point for the CLI."""
    print(f"Legal Swiss support v{__version__}")
    print("Hello World!")
    print("CLI implementation coming soon...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
