#!/usr/bin/env python3
"""
Kitty kitten for getting the current layout name.
Based on vim-kitty-navigator by knubie.
"""


def main():
    pass


def handle_result(args, result, target_window_id, boss):
    """Return the current layout name."""
    return boss.active_tab.current_layout.name


handle_result.no_ui = True
