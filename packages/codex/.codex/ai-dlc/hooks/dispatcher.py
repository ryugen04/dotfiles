#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from aidlc.cli import main


if __name__ == "__main__":
    if len(sys.argv) > 1 and "CODEX_HOOK_EVENT_NAME" not in os.environ:
        os.environ["CODEX_HOOK_EVENT_NAME"] = sys.argv[1]
    raise SystemExit(main(["hook-dispatch"]))
