#!/usr/bin/env python3
"""Custom kitty tab bar with cheap snapshots and async repo status."""

from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from kitty.fast_data_types import Screen, add_timer, get_boss, get_options, wcswidth
from kitty.rgb import to_color
from kitty.tab_bar import DrawData, ExtraData, TabAccessor, TabBarData
from kitty.utils import color_as_int

try:
    opts = get_options()
except Exception:
    opts = None


def _rgb_from_hex(hex_color: str) -> int:
    parsed = to_color(hex_color)
    if parsed is None:
        return 0
    return (color_as_int(parsed) << 8) | 2


def _opt_color(name: str, fallback: str) -> int:
    if opts is not None:
        try:
            return (color_as_int(getattr(opts, name)) << 8) | 2
        except Exception:
            pass
    return _rgb_from_hex(fallback)


def _color(hex_color: str, fallback: int) -> int:
    value = _rgb_from_hex(hex_color)
    return value if value else fallback


BAR_BG = 0
FG = _opt_color("color7", "#c7c7c7")
BG = _opt_color("background", "#16171e")
ACTIVE = _opt_color("active_tab_background", "#2f6f73")
INACTIVE = _opt_color("inactive_tab_background", "#303238")
CYAN = _opt_color("color4", "#9bb8dc")
MAGENTA = _opt_color("color5", "#baace2")
YELLOW = _opt_color("color3", "#f5b78a")
GREEN = _opt_color("color2", "#83ac8e")
RED = _opt_color("color1", "#e68e8e")
DIM = _opt_color("color8", "#676767")

SOFT_BG = _color("#20212b", BG)
ACTIVE_TAB = _color("#c7a6ff", ACTIVE)
INACTIVE_TAB = _color("#5f6070", INACTIVE)
LEFT_COLOR = _color("#8aadf4", CYAN)
RIGHT_COLOR = _color("#f5bde6", MAGENTA)
OK_COLOR = _color("#a6da95", GREEN)
ERR_COLOR = _color("#ed8796", RED)
DIM_COLOR = _color("#7f849c", DIM)

REFRESH_TIME = 1.0
REPO_TTL = 45.0
ERROR_TTL = 15.0
MAX_LENGTH_PATH = 3
# 中央タブを省略表示する際、タブ名は先頭 NAME_ABBREV 桁までに切り詰める。
# AI エージェントのマーカー (index + claude/codex アイコン) は icon 側に置くため常に残る。
NAME_ABBREV = 10
# cell.draw / cell.length に「クリップ不要」を伝えるための十分大きな値
FULL_SIZE = 10_000

FOLDER_ICON = " "
BRANCH_ICON = " "
PR_ICON = " "
CLOCK_ICON = "󰥔 "
CODEX_ICON = ""
CLAUDE_ICON = "󰋦"
SHELL_ICON = ""
DOT_IDLE = "·"
DOT_WAITING = "?"
DOT_RUNNING = "󰐊"
DOT_ERROR = "󰅚"
DIRTY_ICON = "✎"
LOADING_ICON = "…"

GENERIC_TITLES = {
    "",
    "bash",
    "zsh",
    "fish",
    "nu",
    "sh",
    "nvim",
    "vim",
    "claude",
    "claude code",
    "codex",
    "openai codex",
}

RepoStatus = dict[str, Any]
repo_cache: dict[str, RepoStatus] = {}
in_flight: set[str] = set()
result_queue: queue.Queue[tuple[str, RepoStatus]] = queue.Queue()

tab_snapshots: list["TabSnapshot"] = []
# for_layout パスで収集した全タブ。real パスの先頭で tab_snapshots に流し込む。
layout_snapshots: list["TabSnapshot"] = []
# 中央タブごとの描画セル範囲 (1-based index -> (start_col, end_col))。
# kitty のクリック判定 (tab_id_at) 用に draw_tab がこの範囲を返す。
center_tab_ranges: dict[int, tuple[int, int] | None] = {}
active_index = 0
timer_id = None
clock_minute = ""


class TabSnapshot:
    def __init__(
        self,
        index: int,
        tab: TabBarData,
        cwd: Path | None,
        exe: str,
        oldest_exe: str,
    ) -> None:
        self.index = index
        self.tab = tab
        self.tab_id = tab.tab_id
        self.is_active = tab.is_active
        self.needs_attention = tab.needs_attention
        self.has_activity = tab.has_activity_since_last_focus
        self.title = str(tab.title or "")
        self.session_name = tab.session_name or "none"
        self.cwd = cwd
        self.exe = exe
        self.oldest_exe = oldest_exe
        self.name = _tab_name(self)
        self.marker = _agent_marker(self)


class RepoSnapshot:
    def __init__(self, root: Path, git_dir: Path, branch: str | None, cached: RepoStatus) -> None:
        self.root = root
        self.git_dir = git_dir
        self.key = str(root)
        self.branch = str(cached.get("branch") or branch or "")
        self.dirty = bool(cached.get("dirty"))
        self.pr_number = cached.get("pr_number")
        self.pr_state = str(cached.get("pr_state") or "open")
        self.loading = bool(cached.get("loading"))


class Cell:
    def __init__(
        self,
        icon: str,
        text: str | None,
        bg: int = SOFT_BG,
        fg: int = FG,
        color: int = ACTIVE_TAB,
        separator: str = "",
        border: tuple[str, str] = ("", ""),
    ) -> None:
        self.icon = icon
        self.text = text
        self.bg = bg
        self.fg = fg
        self.color = color
        self.separator = separator
        self.border = border
        self.text_length_overhead = wcswidth(self.border[0] + self.border[1] + self.separator + self.icon) + 1

    def _fit_text(self, max_size: int) -> str | None:
        if self.text is None:
            return None
        if max_size <= 0:
            return ""
        return _clip_end(self.text, max_size)

    def draw(self, screen: Screen, max_size: int) -> None:
        text = self._fit_text(max_size - self.text_length_overhead)
        if text is None:
            return

        screen.cursor.dim = False
        screen.cursor.bold = False
        screen.cursor.italic = False
        screen.cursor.bg = BAR_BG
        screen.cursor.fg = self.color
        screen.draw(self.border[0])

        screen.cursor.bg = self.color
        screen.cursor.fg = BG
        screen.cursor.bold = True
        screen.draw(self.icon)
        screen.cursor.bold = False

        if text == "":
            screen.cursor.bg = BAR_BG
            screen.cursor.fg = self.color
            screen.draw(self.border[1])
            return

        screen.cursor.bg = self.bg
        screen.cursor.fg = self.color
        screen.draw(self.separator)
        screen.cursor.fg = self.fg
        screen.draw(f" {text}")
        screen.cursor.fg = self.bg
        screen.cursor.bg = BAR_BG
        screen.draw(self.border[1])

    def length(self, max_size: int) -> int:
        text = self._fit_text(max_size - self.text_length_overhead)
        if text is None:
            return 0
        if text == "":
            return wcswidth(self.icon + self.border[0] + self.border[1])
        return wcswidth(text) + self.text_length_overhead


def _clip_end(text: str, max_size: int) -> str | None:
    if max_size < 1:
        return None
    if wcswidth(text) <= max_size:
        return text
    out = ""
    used = 0
    for ch in text:
        width = max(0, wcswidth(ch))
        if used + width + 1 > max_size:
            break
        out += ch
        used += width
    return out + "…" if out else None


def _clip_middle(text: str, max_size: int) -> str | None:
    if max_size < 1:
        return None
    if wcswidth(text) <= max_size:
        return text
    if max_size <= 3:
        return _clip_end(text, max_size)
    left_size = max(1, (max_size - 1) // 2)
    right_size = max(1, max_size - 1 - left_size)
    left = _clip_end(text, left_size)
    if left is None:
        return None
    if left.endswith("…"):
        left = left[:-1]
    right = ""
    used = 0
    for ch in reversed(text):
        width = max(0, wcswidth(ch))
        if used + width > right_size:
            break
        right = ch + right
        used += width
    return f"{left}…{right}" if right else _clip_end(text, max_size)


def _tab_accessor_snapshot(tab: TabBarData) -> tuple[Path | None, str, str]:
    try:
        accessor = TabAccessor(tab.tab_id)
    except Exception:
        return None, "", ""

    cwd: Path | None = None
    try:
        active_wd = accessor.active_wd
        if active_wd:
            cwd = Path(str(active_wd)).expanduser()
    except Exception:
        cwd = None

    exe = ""
    oldest_exe = ""
    try:
        value = accessor.active_exe
        exe = Path(str(value)).name if value else ""
    except Exception:
        pass
    try:
        value = accessor.active_oldest_exe
        oldest_exe = Path(str(value)).name if value else ""
    except Exception:
        pass
    return cwd, exe, oldest_exe


def _compact_path(path: Path, max_size: int) -> str | None:
    home = Path(os.getenv("HOME", "")).expanduser()
    try:
        display = Path("~") / path.relative_to(home) if home and path.is_relative_to(home) else path
    except Exception:
        display = path

    parts = list(display.parts)
    if not parts:
        return None
    compressed = False
    if len(parts) > MAX_LENGTH_PATH:
        compressed = True
        parts = [parts[0], ".."] + parts[-MAX_LENGTH_PATH:]

    parts_cnt = 1 + int(compressed)
    while parts_cnt != len(parts):
        candidate = "/".join(parts[0 : 1 + int(compressed)] + parts[parts_cnt:])
        if wcswidth(candidate) <= max_size:
            return candidate
        parts_cnt += 1
    return _clip_end(parts[-1], max_size)


def _explicit_title(snapshot: TabSnapshot) -> str | None:
    title = snapshot.title.strip()
    if title.startswith("#"):
        return title[1:].strip() or None
    normalized = title.lstrip("* ").strip().lower()
    if normalized in GENERIC_TITLES:
        return None
    if "/" in title or title.startswith("~"):
        return None
    return title or None


def _tab_name(snapshot: TabSnapshot) -> str:
    explicit = _explicit_title(snapshot)
    if explicit:
        return explicit
    if snapshot.cwd is not None:
        return snapshot.cwd.name or str(snapshot.cwd)
    return snapshot.exe or snapshot.oldest_exe or "?"


def _agent_marker(snapshot: TabSnapshot) -> str:
    haystack = " ".join([snapshot.title, snapshot.exe, snapshot.oldest_exe]).lower()
    if "claude" in haystack:
        icon = CLAUDE_ICON
    elif "codex" in haystack:
        icon = CODEX_ICON
    else:
        icon = SHELL_ICON

    if snapshot.needs_attention:
        return f"{icon}{DOT_ERROR}"
    if snapshot.has_activity:
        return f"{icon}{DOT_RUNNING}"
    if icon in {CODEX_ICON, CLAUDE_ICON}:
        return f"{icon}{DOT_WAITING}"
    return f"{icon}{DOT_IDLE}"


def _git_dir_for(root: Path) -> Path | None:
    dotgit = root / ".git"
    if dotgit.is_dir():
        return dotgit
    if dotgit.is_file():
        try:
            text = dotgit.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            return None
        prefix = "gitdir:"
        if text.startswith(prefix):
            path = Path(text[len(prefix) :].strip())
            return path if path.is_absolute() else (root / path).resolve()
    return None


def _repo_for(path: Path | None) -> tuple[Path, Path] | None:
    if path is None:
        return None
    current = path if path.is_dir() else path.parent
    for candidate in [current, *current.parents]:
        git_dir = _git_dir_for(candidate)
        if git_dir is not None:
            return candidate, git_dir
    return None


def _branch_from_git_dir(git_dir: Path) -> str | None:
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        return None
    ref_prefix = "ref: refs/heads/"
    if head.startswith(ref_prefix):
        return head[len(ref_prefix) :]
    if head.startswith("ref: "):
        return head[5:].split("/")[-1]
    return head[:7] if head else None


def _run(cmd: list[str], cwd: Path, timeout: float = 2.0) -> str | None:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception:
        return None
    if proc.returncode != 0 and not proc.stdout.strip():
        return None
    return proc.stdout.strip()


def _worker(repo: Path, git_dir: Path) -> None:
    status: RepoStatus = {"updated_at": time.time(), "loading": False}
    branch = _branch_from_git_dir(git_dir)
    if branch:
        status["branch"] = branch

    dirty = _run(["git", "status", "--porcelain"], repo, timeout=1.5)
    status["dirty"] = bool(dirty)

    pr_raw = None
    if branch:
        pr_raw = _run(["gh", "pr", "view", branch, "--json", "number,state,isDraft"], repo, timeout=2.5)
        if not pr_raw:
            pr_raw = _run(["gh", "pr", "list", "--head", branch, "--json", "number,state,isDraft", "--limit", "1"], repo, timeout=2.5)
    if pr_raw:
        try:
            parsed = json.loads(pr_raw)
            pr = parsed[0] if isinstance(parsed, list) and parsed else parsed
            if isinstance(pr, dict):
                state = str(pr.get("state") or "open").lower()
                if pr.get("isDraft"):
                    state = "draft"
                status["pr_number"] = pr.get("number")
                status["pr_state"] = state
        except Exception:
            status["error_at"] = time.time()

    result_queue.put((str(repo), status))


def _request_repo(repo: Path, git_dir: Path, branch: str | None) -> None:
    key = str(repo)
    now = time.time()
    cached = repo_cache.get(key)
    if key in in_flight:
        return
    if cached is not None:
        ttl = ERROR_TTL if cached.get("error_at") else REPO_TTL
        if now - float(cached.get("updated_at", 0)) < ttl:
            return

    in_flight.add(key)
    existing = repo_cache.setdefault(key, {"updated_at": now})
    if branch:
        existing["branch"] = branch
    existing["loading"] = True
    thread = threading.Thread(target=_worker, args=(repo, git_dir), daemon=True)
    thread.start()


def _repo_snapshot(active: TabSnapshot | None) -> RepoSnapshot | None:
    if active is None:
        return None
    repo_info = _repo_for(active.cwd)
    if repo_info is None:
        return None
    repo, git_dir = repo_info
    branch = _branch_from_git_dir(git_dir)
    _request_repo(repo, git_dir, branch)
    cached = repo_cache.get(str(repo), {})
    return RepoSnapshot(repo, git_dir, branch, cached)


def _tab_cell(snapshot: TabSnapshot) -> Cell:
    color = ACTIVE_TAB if snapshot.is_active else INACTIVE_TAB
    # index と AI マーカーは icon (常時描画される chip) に入れ、省略対象の name のみ text にする。
    icon = f"{snapshot.index} {snapshot.marker}"
    return Cell(icon, snapshot.name, color=color)


def _left_cell(active: TabSnapshot) -> Cell:
    text = _compact_path(active.cwd, 36) if active.cwd is not None else None
    return Cell(FOLDER_ICON, text, color=LEFT_COLOR)


def _right_cells(repo: RepoSnapshot | None, active: TabSnapshot | None) -> list[Cell]:
    cells: list[Cell] = []
    if repo is not None and repo.branch:
        dirty = f" {DIRTY_ICON}" if repo.dirty else ""
        cells.append(Cell(BRANCH_ICON, f"{repo.branch}{dirty}", color=RIGHT_COLOR))
        if repo.pr_number:
            cells.append(Cell(PR_ICON, f"#{repo.pr_number}", color=RIGHT_COLOR))
        elif repo.loading:
            cells.append(Cell(PR_ICON, LOADING_ICON, color=RIGHT_COLOR))
    cells.append(Cell(CLOCK_ICON, time.strftime("%H:%M"), color=DIM_COLOR))
    return cells


def _layout_width(cells: list[Cell], sizes: list[int]) -> int:
    """sizes に従って中央タブ群を描画したときの総幅 (セパレータ込み) を返す。

    sizes[i] は cell.draw に渡す max_size。負値はそのセルを非表示にする。
    """
    total = 0
    first = True
    for cell, size in zip(cells, sizes):
        if size < 0:
            continue
        width = cell.length(size)
        if width <= 0:
            continue
        total += width + (0 if first else 1)
        first = False
    return total


def _center_layout(cells: list[Cell], max_width: int) -> tuple[list[int], int]:
    """中央タブ群の各セルに割り当てる max_size のリストと総幅を返す。

    優先順位 (= 中央をできる限り表示する戦略):
      1. 全タブをフル名で表示できるならそうする
      2. 入らないなら、全タブ一律に name を k 桁 (NAME_ABBREV..1) まで詰めて最大 k で表示
      3. それでも入らないなら icon のみ (index + AI マーカーは残る)
      4. 限界ならアクティブタブのみ表示
    """
    n = len(cells)
    if n == 0:
        return [], 0

    sizes = [FULL_SIZE] * n
    total = _layout_width(cells, sizes)
    if total <= max_width:
        return sizes, total

    for k in range(NAME_ABBREV, 0, -1):
        sizes = [cell.text_length_overhead + k for cell in cells]
        total = _layout_width(cells, sizes)
        if total <= max_width:
            return sizes, total

    sizes = [0] * n
    total = _layout_width(cells, sizes)
    if total <= max_width:
        return sizes, total

    sizes = [-1] * n
    if cells[active_index].length(FULL_SIZE) <= max_width:
        sizes[active_index] = FULL_SIZE
        return sizes, cells[active_index].length(FULL_SIZE)
    sizes[active_index] = 0
    return sizes, cells[active_index].length(0)


def _draw_center(screen: Screen, cells: list[Cell], sizes: list[int]) -> None:
    """中央タブ群を描画しつつ、各タブのセル範囲を center_tab_ranges に記録する。"""
    first = True
    for cell, snapshot, size in zip(cells, tab_snapshots, sizes):
        if size < 0:
            center_tab_ranges[snapshot.index] = None
            continue
        if not first:
            screen.draw(" ")
        start = screen.cursor.x
        cell.draw(screen, size)
        center_tab_ranges[snapshot.index] = (start, screen.cursor.x)
        first = False


def _cells_width(cells: list[Cell], max_width: int) -> int:
    width = 0
    for cell in cells:
        length = cell.length(max_width)
        if length:
            width += length + (1 if width else 0)
    return width


def draw_right(screen: Screen, cells: list[Cell], max_width: int) -> None:
    visible: list[tuple[Cell, int]] = []
    total = 0
    for cell in cells:
        remaining = max_width - total - (1 if visible else 0)
        length = cell.length(remaining)
        if length == 0:
            continue
        if total + (1 if visible else 0) + length > max_width:
            continue
        visible.append((cell, remaining))
        total += (1 if len(visible) > 1 else 0) + length

    if total <= 0:
        return
    offset = max(0, screen.columns - total - screen.cursor.x)
    screen.draw(" " * offset)
    for idx, (cell, max_cell) in enumerate(visible):
        if idx:
            screen.draw(" ")
        cell.draw(screen, max_cell)


def _drain_results() -> bool:
    changed = False
    while True:
        try:
            key, status = result_queue.get_nowait()
        except queue.Empty:
            break
        previous = repo_cache.get(key, {})
        repo_cache[key] = {**previous, **status, "loading": False}
        in_flight.discard(key)
        changed = True
    return changed


def redraw_tab_bar(_: float) -> None:
    global clock_minute
    changed = _drain_results()
    minute = time.strftime("%H:%M")
    if minute != clock_minute:
        clock_minute = minute
        changed = True
    boss = get_boss()
    tm = boss.active_tab_manager if boss is not None else None
    if changed and tm is not None:
        tm.mark_tab_bar_dirty()


def _draw_all(screen: Screen) -> None:
    if not tab_snapshots:
        return

    active = tab_snapshots[active_index] if 0 <= active_index < len(tab_snapshots) else tab_snapshots[0]
    repo = _repo_snapshot(active)
    left = _left_cell(active)
    center_cells = [_tab_cell(snapshot) for snapshot in tab_snapshots]
    right_cells = _right_cells(repo, active)

    screen.cursor.x = 0
    screen.cursor.bg = BAR_BG
    screen.cursor.fg = FG

    left_max = min(36, max(8, screen.columns // 4))
    left_width = left.length(left_max)
    right_budget = max(0, screen.columns - max(left_width + 2, screen.columns // 2))
    right_width = min(_cells_width(right_cells, right_budget), right_budget)
    center_max = max(0, screen.columns - left_width - right_width - 4)
    sizes, center_width = _center_layout(center_cells, center_max)

    center_start = max(left_width + 1, (screen.columns - center_width) // 2)
    right_start = screen.columns - right_width if right_width else screen.columns
    if center_start + center_width >= right_start:
        center_start = max(left_width + 1, right_start - center_width - 1)

    left.draw(screen, left_max)
    if screen.cursor.x < center_start:
        screen.draw(" " * (center_start - screen.cursor.x))
    _draw_center(screen, center_cells, sizes)
    draw_right(screen, right_cells, max(0, screen.columns - screen.cursor.x - 1))

    if screen.cursor.x < screen.columns:
        screen.draw(" " * (screen.columns - screen.cursor.x))


def draw_tab(
    draw_data: DrawData,
    screen: Screen,
    tab: TabBarData,
    before: int,
    max_title_length: int,
    index: int,
    is_last: bool,
    extra_data: ExtraData,
) -> int:
    global active_index, tab_snapshots, layout_snapshots, center_tab_ranges, timer_id

    if timer_id is None:
        timer_id = add_timer(redraw_tab_bar, REFRESH_TIME, True)

    # kitty は update() で「レイアウト計測パス (for_layout=True)」→「実描画パス」の順に
    # 全タブを 2 周する。レイアウトパスで全 TabSnapshot を集めておき、実描画パスの先頭
    # (index==1) で全体を 1 度に描画する。これにより各 draw_tab が「そのタブの正しい
    # セル終端 x」を返せるようになり、kitty のクリック判定 (tab_id_at) が正しく機能する。
    if getattr(extra_data, "for_layout", False):
        if index == 1:
            layout_snapshots = []
        cwd, exe, oldest_exe = _tab_accessor_snapshot(tab)
        layout_snapshots.append(TabSnapshot(index, tab, cwd, exe, oldest_exe))
        return screen.cursor.x

    if index == 1:
        tab_snapshots = list(layout_snapshots)
        active_index = next((i for i, s in enumerate(tab_snapshots) if s.is_active), 0)
        center_tab_ranges = {}
        _draw_all(screen)

    # 実描画は index==1 で完了済み。各タブは記録済みのセル範囲の終端 x を返し、
    # cursor.x をそこへ移すことで kitty に連続したクリック領域を構築させる。
    rng = center_tab_ranges.get(index)
    if is_last:
        # 最終タブは行末まで占有させる。これで kitty の erase_in_line(0) が右側
        # (git/PR/clock) を消さない。
        end = screen.columns
    elif rng is not None:
        end = rng[1]
    else:
        end = screen.cursor.x
    end = max(screen.cursor.x, min(end, screen.columns))
    screen.cursor.x = end
    return end
