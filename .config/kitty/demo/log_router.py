#!/usr/bin/env python3
"""
log_router.py - ログを分類・フィルタリングするツール

kittyの各タブにログを分配するためのルーター。
ログレベルやパターンでフィルタリングし、色付けして出力。

使用例:
    # ファイルをリアルタイム監視
    python log_router.py -f /var/log/app.log

    # 特定レベルのみ表示
    python log_router.py -f /var/log/app.log --level ERROR

    # パターンでフィルタ
    python log_router.py -f /var/log/app.log --pattern "user_id=123"

    # 要約モード（Claude Code解析用）
    python log_router.py /var/log/app.log --summarize
"""

import sys
import re
import argparse
import time
from datetime import datetime
from collections import defaultdict
from typing import Generator, Optional

# ANSI色コード
COLORS = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "WARN": "\033[33m",       # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[35m",   # Magenta
    "FATAL": "\033[35m",      # Magenta
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
    "DIM": "\033[2m",
}

# ログレベルの正規表現パターン
LOG_LEVEL_PATTERN = re.compile(
    r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b",
    re.IGNORECASE
)

# HTTP ステータスコードの正規表現
HTTP_STATUS_PATTERN = re.compile(r'\b([45]\d{2})\b')

# タイムスタンプの正規表現（複数フォーマット対応）
TIMESTAMP_PATTERNS = [
    re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'),
    re.compile(r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}'),
    re.compile(r'\[\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\]'),
]


def detect_log_level(line: str) -> str:
    """ログ行からログレベルを検出"""
    match = LOG_LEVEL_PATTERN.search(line)
    if match:
        return match.group(1).upper()

    # HTTPステータスコードでエラーを検出
    status_match = HTTP_STATUS_PATTERN.search(line)
    if status_match:
        status = int(status_match.group(1))
        if status >= 500:
            return "ERROR"
        elif status >= 400:
            return "WARNING"

    return "INFO"


def colorize_line(line: str, level: str) -> str:
    """ログ行に色を付ける"""
    color = COLORS.get(level, COLORS["RESET"])
    return f"{color}{line}{COLORS['RESET']}"


def follow_file(filepath: str) -> Generator[str, None, None]:
    """ファイルをtail -fのようにフォロー"""
    with open(filepath, 'r') as f:
        # 最後の10行から開始
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(max(0, file_size - 4096))
        lines = f.readlines()
        for line in lines[-10:]:
            yield line.rstrip()

        # 新しい行を監視
        while True:
            line = f.readline()
            if line:
                yield line.rstrip()
            else:
                time.sleep(0.1)


def read_file(filepath: str) -> Generator[str, None, None]:
    """ファイルを読み込む"""
    with open(filepath, 'r') as f:
        for line in f:
            yield line.rstrip()


def filter_by_level(lines: Generator, min_level: str) -> Generator[str, None, None]:
    """指定レベル以上のログのみをフィルタ"""
    level_order = ["DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"]
    min_index = level_order.index(min_level.upper()) if min_level.upper() in level_order else 0

    for line in lines:
        level = detect_log_level(line)
        level_index = level_order.index(level) if level in level_order else 1
        if level_index >= min_index:
            yield line


def filter_by_pattern(lines: Generator, pattern: str) -> Generator[str, None, None]:
    """パターンにマッチする行のみをフィルタ"""
    regex = re.compile(pattern, re.IGNORECASE)
    for line in lines:
        if regex.search(line):
            yield line


def summarize_logs(filepath: str) -> dict:
    """ログファイルを要約（Claude Code解析用）"""
    stats = {
        "total_lines": 0,
        "by_level": defaultdict(int),
        "errors": [],
        "warnings": [],
        "http_errors": [],
        "time_range": {"start": None, "end": None},
    }

    with open(filepath, 'r') as f:
        for line in f:
            line = line.rstrip()
            stats["total_lines"] += 1

            # ログレベル集計
            level = detect_log_level(line)
            stats["by_level"][level] += 1

            # エラー・警告を収集（最大10件）
            if level in ("ERROR", "CRITICAL", "FATAL") and len(stats["errors"]) < 10:
                stats["errors"].append(line[:200])
            elif level in ("WARNING", "WARN") and len(stats["warnings"]) < 10:
                stats["warnings"].append(line[:200])

            # HTTPエラーを収集
            status_match = HTTP_STATUS_PATTERN.search(line)
            if status_match and len(stats["http_errors"]) < 10:
                status = int(status_match.group(1))
                if status >= 400:
                    stats["http_errors"].append(f"[{status}] {line[:150]}")

            # タイムスタンプを抽出
            for pattern in TIMESTAMP_PATTERNS:
                match = pattern.search(line)
                if match:
                    ts = match.group(0)
                    if stats["time_range"]["start"] is None:
                        stats["time_range"]["start"] = ts
                    stats["time_range"]["end"] = ts
                    break

    return stats


def print_summary(stats: dict) -> None:
    """要約を出力"""
    print(f"\n{COLORS['BOLD']}=== Log Summary ==={COLORS['RESET']}\n")

    print(f"Total Lines: {stats['total_lines']}")
    if stats["time_range"]["start"]:
        print(f"Time Range: {stats['time_range']['start']} ~ {stats['time_range']['end']}")

    print(f"\n{COLORS['BOLD']}Level Distribution:{COLORS['RESET']}")
    for level, count in sorted(stats["by_level"].items()):
        color = COLORS.get(level, COLORS["RESET"])
        bar = "#" * min(count // 10, 50)
        print(f"  {color}{level:10}{COLORS['RESET']}: {count:5} {bar}")

    if stats["errors"]:
        print(f"\n{COLORS['BOLD']}{COLORS['ERROR']}Recent Errors ({len(stats['errors'])}):{COLORS['RESET']}")
        for err in stats["errors"][:5]:
            print(f"  {COLORS['DIM']}- {err}{COLORS['RESET']}")

    if stats["http_errors"]:
        print(f"\n{COLORS['BOLD']}{COLORS['WARNING']}HTTP Errors ({len(stats['http_errors'])}):{COLORS['RESET']}")
        for err in stats["http_errors"][:5]:
            print(f"  {COLORS['DIM']}- {err}{COLORS['RESET']}")


def generate_claude_prompt(stats: dict, filepath: str) -> str:
    """Claude Code用の解析プロンプトを生成"""
    prompt = f"""以下のログファイルを分析し、問題点と推奨対応を報告してください。

## ログ概要
- ファイル: {filepath}
- 総行数: {stats['total_lines']}
- 時間範囲: {stats['time_range']['start']} ~ {stats['time_range']['end']}

## レベル分布
"""
    for level, count in sorted(stats["by_level"].items()):
        prompt += f"- {level}: {count}\n"

    if stats["errors"]:
        prompt += "\n## エラーサンプル\n```\n"
        for err in stats["errors"][:5]:
            prompt += f"{err}\n"
        prompt += "```\n"

    prompt += """
## 期待する出力
1. 主要な問題点（優先度順）
2. 推定される原因
3. 推奨される対応策
4. 追加で確認すべき観測点
"""
    return prompt


def main():
    parser = argparse.ArgumentParser(
        description="Log Router - ログの分類・フィルタリングツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
    # リアルタイム監視（色付き）
    python log_router.py -f /var/log/app.log

    # エラーのみ表示
    python log_router.py -f /var/log/app.log --level ERROR

    # 要約を出力（Claude Code用）
    python log_router.py /var/log/app.log --summarize

    # Claude用プロンプト生成
    python log_router.py /var/log/app.log --claude-prompt
        """
    )

    parser.add_argument("file", help="ログファイルのパス")
    parser.add_argument("-f", "--follow", action="store_true",
                        help="ファイルをフォロー（tail -f相当）")
    parser.add_argument("--level", type=str, default=None,
                        help="最小ログレベル (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--pattern", type=str, default=None,
                        help="フィルタパターン（正規表現）")
    parser.add_argument("--summarize", action="store_true",
                        help="ログを要約して出力")
    parser.add_argument("--claude-prompt", action="store_true",
                        help="Claude Code用の解析プロンプトを生成")
    parser.add_argument("--no-color", action="store_true",
                        help="色付けを無効化")

    args = parser.parse_args()

    # 要約モード
    if args.summarize or args.claude_prompt:
        stats = summarize_logs(args.file)
        if args.claude_prompt:
            print(generate_claude_prompt(stats, args.file))
        else:
            print_summary(stats)
        return

    # ストリーミングモード
    try:
        if args.follow:
            lines = follow_file(args.file)
        else:
            lines = read_file(args.file)

        # フィルタ適用
        if args.level:
            lines = filter_by_level(lines, args.level)
        if args.pattern:
            lines = filter_by_pattern(lines, args.pattern)

        # 出力
        for line in lines:
            level = detect_log_level(line)
            if args.no_color:
                print(line)
            else:
                print(colorize_line(line, level))

    except KeyboardInterrupt:
        print(f"\n{COLORS['DIM']}Interrupted{COLORS['RESET']}")
    except FileNotFoundError:
        print(f"{COLORS['ERROR']}Error: File not found: {args.file}{COLORS['RESET']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
