#!/usr/bin/env python3
"""透明度を切り替えるkitten"""

from typing import List
from kitty.boss import Boss


def main(args: List[str]) -> str:
    return ""


def handle_result(args: List[str], answer: str, target_window_id: int, boss: Boss) -> None:
    """透明度を切り替える"""
    import kitty.fast_data_types as f

    # 透明度の値を設定
    transparent = 0.6
    opaque = 1.0

    # 現在フォーカスされているOSウィンドウIDを取得
    os_window_id = f.current_focused_os_window_id()

    # 現在の透明度を取得
    current_opacity = f.background_opacity_of(os_window_id)

    # 透明度を切り替え（現在の透明度が0.8未満なら不透明に、そうでなければ透明に）
    if current_opacity < 0.8:
        new_opacity = opaque
    else:
        new_opacity = transparent

    # 透明度を設定
    boss.set_background_opacity(str(new_opacity))


handle_result.no_ui = True
