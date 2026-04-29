from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_data(path: Path) -> Any:
    text = read_text(path)
    if yaml is not None:
        return yaml.safe_load(text) or {}
    return json.loads(text)


def write_data(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    if yaml is not None:
        rendered = yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=False,
            default_flow_style=False,
        )
    else:  # pragma: no cover
        rendered = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    path.write_text(rendered, encoding="utf-8")


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = read_text(path)
    if not text.startswith("---\n"):
        return {}, text
    _, fm, body = text.split("---\n", 2)
    if yaml is not None:
        data = yaml.safe_load(fm) or {}
    else:  # pragma: no cover
        data = json.loads(fm)
    return data, body


def write_frontmatter(path: Path, metadata: dict[str, Any], body: str) -> None:
    ensure_dir(path.parent)
    if yaml is not None:
        fm = yaml.safe_dump(
            metadata,
            sort_keys=False,
            allow_unicode=False,
            default_flow_style=False,
        ).rstrip()
    else:  # pragma: no cover
        fm = json.dumps(metadata, indent=2, ensure_ascii=True)
    path.write_text(f"---\n{fm}\n---\n{body.lstrip()}", encoding="utf-8")
