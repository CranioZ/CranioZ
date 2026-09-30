"""Entry point for the CranioZ CLI."""

from __future__ import annotations

import sys


def main() -> int:
    """Run the CranioZ application."""
    print(f"CranioZ {_get_version()} — starting...")
    # TODO: launch the Qt application (to be implemented in 0.3)
    return 0


def _get_version() -> str:
    from cranioz import __version__

    return __version__


if __name__ == "__main__":
    sys.exit(main())