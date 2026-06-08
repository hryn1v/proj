#!/usr/bin/env python3
"""Convenience launcher for the Rental Management System CLI.

Run any of:

    python rms.py
    python -m rms
    python -m src.cli
"""
from __future__ import annotations

from src.cli.repl import main

if __name__ == "__main__":
    main()
