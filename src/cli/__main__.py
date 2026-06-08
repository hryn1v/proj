"""Module entry point so the CLI can be launched via ``python -m src.cli``."""
from __future__ import annotations

from src.cli.repl import main

if __name__ == "__main__":
    main()
