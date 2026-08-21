"""Backward-compatible entry point for the packaged CLI."""

from simple_port_scanner.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
