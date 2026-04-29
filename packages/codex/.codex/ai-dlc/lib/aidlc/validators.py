from __future__ import annotations

from pathlib import Path

from .overlay import validate_overlay
from .state import validate


def assert_overlay(root: Path) -> None:
    errors = validate_overlay(root)
    if errors:
        raise ValueError("\n".join(errors))


def assert_workspace(root: Path) -> None:
    errors = validate(root)
    if errors:
        raise ValueError("\n".join(errors))
