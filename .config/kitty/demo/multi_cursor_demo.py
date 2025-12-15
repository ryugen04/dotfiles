#!/usr/bin/env python3
"""
Multiple Cursors Protocol デモ
kitty 0.43+ で追加された世界初のターミナルネイティブ複数カーソル機能

参考: https://sw.kovidgoyal.net/kitty/multiple-cursors-protocol/
"""
import sys
import time
import os
import math

# ANSI色
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
BLUE = "\033[34m"
WHITE = "\033[97m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# 背景色
BG_BLUE = "\033[44m"
BG_GREEN = "\033[42m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_RESET = "\033[49m"

def clear_screen():
    print("\033[2J\033[H", end="")

def move_cursor(y, x):
    print(f"\033[{y};{x}H", end="")

def show_multi_cursor(shape, y, x):
    """指定位置に追加カーソルを表示"""
    print(f"\033[>{shape};2:{y}:{x} q", end="")
    sys.stdout.flush()

def show_multi_cursors(shape, positions):
    """複数位置にカーソルを表示"""
    coords = ";".join([f"2:{y}:{x}" for y, x in positions])
    print(f"\033[>{shape};{coords} q", end="")
    sys.stdout.flush()

def clear_multi_cursors():
    """全ての追加カーソルをクリア"""
    print("\033[>0;4 q", end="")
    sys.stdout.flush()

def draw_box(row, col, width, height, title="", color=CYAN):
    """ボックスを描画"""
    move_cursor(row, col)
    print(f"{color}╭{'─' * (width - 2)}╮{RESET}")
    if title:
        title_str = f" {title} "
        padding = width - 4 - len(title)
        move_cursor(row, col + 2)
        print(f"{color}{BOLD}{title_str}{RESET}")
    for i in range(1, height - 1):
        move_cursor(row + i, col)
        print(f"{color}│{' ' * (width - 2)}│{RESET}")
    move_cursor(row + height - 1, col)
    print(f"{color}╰{'─' * (width - 2)}╯{RESET}")

def print_header():
    clear_screen()
    print(f"{CYAN}{'━' * 65}{RESET}")
    print(f"{CYAN}  ✨ Multiple Cursors Protocol Demo{RESET}")
    print(f"{CYAN}  kitty 0.43+ 世界初のターミナルネイティブ複数カーソル{RESET}")
    print(f"{CYAN}{'━' * 65}{RESET}")
    print()

def demo_intro():
    """イントロ: カーソル形状一覧"""
    print_header()

    print(f"{GREEN}[Demo 1]{RESET} カーソル形状一覧")
    print()
    print("  kittyは4種類のカーソル形状をサポートしています:")
    print()

    base_row = 10
    shapes = [
        (1, "Block", "█", "VSCodeのノーマルモード風"),
        (2, "Beam", "│", "VSCodeの挿入モード風"),
        (3, "Underline", "_", "従来のターミナル風"),
        (29, "Follow", "◆", "メインカーソルと同期"),
    ]

    draw_box(base_row - 1, 3, 60, len(shapes) + 3, "Cursor Shapes", CYAN)

    for i, (shape, name, symbol, desc) in enumerate(shapes):
        row = base_row + i
        move_cursor(row, 6)
        print(f"{YELLOW}Shape {shape:2d}{RESET}: {WHITE}{name:12s}{RESET} {DIM}{symbol}{RESET}  {desc}")
        show_multi_cursor(shape, row, 18)
        time.sleep(0.3)

    move_cursor(base_row + len(shapes) + 3, 3)
    input(f"{DIM}[Enter] 次へ...{RESET}")
    clear_multi_cursors()

def demo_wave():
    """波形パターン"""
    clear_screen()
    print_header()

    print(f"{GREEN}[Demo 2]{RESET} 波形パターン - カーソルウェーブ")
    print()
    print("  複数カーソルで波形を描画します:")
    print()

    base_row = 10
    width = 50

    # 波形を描く
    for frame in range(60):
        positions = []
        for x in range(width):
            # サイン波
            y = int(5 + 4 * math.sin((x + frame) * 0.3))
            positions.append((base_row + y, 5 + x))

        clear_multi_cursors()
        show_multi_cursors(1, positions)  # Block shape
        time.sleep(0.05)

    move_cursor(base_row + 12, 3)
    print(f"{YELLOW}波形アニメーション完了！{RESET}")

    move_cursor(base_row + 14, 3)
    input(f"{DIM}[Enter] 次へ...{RESET}")
    clear_multi_cursors()

def demo_spiral():
    """スパイラルパターン"""
    clear_screen()
    print_header()

    print(f"{GREEN}[Demo 3]{RESET} スパイラルパターン")
    print()
    print("  複数カーソルで渦巻きを描画します:")
    print()

    center_row = 14
    center_col = 35

    for frame in range(80):
        positions = []
        for i in range(20):
            angle = frame * 0.1 + i * 0.5
            radius = 1 + i * 0.4
            x = int(center_col + radius * math.cos(angle) * 2)
            y = int(center_row + radius * math.sin(angle))
            if 5 <= y <= 22 and 5 <= x <= 65:
                positions.append((y, x))

        clear_multi_cursors()
        if positions:
            show_multi_cursors(2, positions)  # Beam shape
        time.sleep(0.05)

    move_cursor(24, 3)
    print(f"{YELLOW}スパイラルアニメーション完了！{RESET}")

    move_cursor(26, 3)
    input(f"{DIM}[Enter] 次へ...{RESET}")
    clear_multi_cursors()

def demo_code_editing():
    """リアルなコード編集シミュレーション"""
    clear_screen()
    print_header()

    print(f"{GREEN}[Demo 4]{RESET} コード編集シミュレーション")
    print()
    print("  VSCode/Neovimのようなマルチカーソル編集:")
    print()

    base_row = 9

    # コードを表示
    code_lines = [
        f"{DIM}1{RESET}  {MAGENTA}const{RESET} {WHITE}user{RESET} = {{ name: {GREEN}'Alice'{RESET}, age: {CYAN}25{RESET} }};",
        f"{DIM}2{RESET}  {MAGENTA}const{RESET} {WHITE}user{RESET} = {{ name: {GREEN}'Bob'{RESET}, age: {CYAN}30{RESET} }};",
        f"{DIM}3{RESET}  {MAGENTA}const{RESET} {WHITE}user{RESET} = {{ name: {GREEN}'Charlie'{RESET}, age: {CYAN}35{RESET} }};",
        f"{DIM}4{RESET}  {MAGENTA}const{RESET} {WHITE}user{RESET} = {{ name: {GREEN}'Diana'{RESET}, age: {CYAN}28{RESET} }};",
        f"{DIM}5{RESET}  {MAGENTA}const{RESET} {WHITE}user{RESET} = {{ name: {GREEN}'Eve'{RESET}, age: {CYAN}22{RESET} }};",
    ]

    draw_box(base_row - 1, 3, 55, len(code_lines) + 2, "editor.js", BLUE)

    for i, line in enumerate(code_lines):
        move_cursor(base_row + i, 5)
        print(line)

    move_cursor(base_row + len(code_lines) + 2, 3)
    input(f"{DIM}[Enter] 'user' を選択...{RESET}")

    # 'user' の位置にカーソルを配置
    positions = [(base_row + i, 15) for i in range(len(code_lines))]
    show_multi_cursors(1, positions)

    move_cursor(base_row + len(code_lines) + 3, 3)
    print(f"{YELLOW}5つの 'user' が選択されました！{RESET}")
    print(f"{DIM}  実際のエディタでは、この状態で入力すると{RESET}")
    print(f"{DIM}  全ての位置に同時にテキストが入力されます{RESET}")

    move_cursor(base_row + len(code_lines) + 7, 3)
    input(f"{DIM}[Enter] タイピングをシミュレート...{RESET}")

    # タイピングシミュレーション
    clear_multi_cursors()
    new_text = "person"
    for char_idx, char in enumerate(new_text):
        code_lines_new = [
            f"{DIM}1{RESET}  {MAGENTA}const{RESET} {WHITE}{new_text[:char_idx+1]}{RESET}" + " " * (6 - char_idx - 1) + f"= {{ name: {GREEN}'Alice'{RESET}, age: {CYAN}25{RESET} }};",
            f"{DIM}2{RESET}  {MAGENTA}const{RESET} {WHITE}{new_text[:char_idx+1]}{RESET}" + " " * (6 - char_idx - 1) + f"= {{ name: {GREEN}'Bob'{RESET}, age: {CYAN}30{RESET} }};",
            f"{DIM}3{RESET}  {MAGENTA}const{RESET} {WHITE}{new_text[:char_idx+1]}{RESET}" + " " * (6 - char_idx - 1) + f"= {{ name: {GREEN}'Charlie'{RESET}, age: {CYAN}35{RESET} }};",
            f"{DIM}4{RESET}  {MAGENTA}const{RESET} {WHITE}{new_text[:char_idx+1]}{RESET}" + " " * (6 - char_idx - 1) + f"= {{ name: {GREEN}'Diana'{RESET}, age: {CYAN}28{RESET} }};",
            f"{DIM}5{RESET}  {MAGENTA}const{RESET} {WHITE}{new_text[:char_idx+1]}{RESET}" + " " * (6 - char_idx - 1) + f"= {{ name: {GREEN}'Eve'{RESET}, age: {CYAN}22{RESET} }};",
        ]
        for i, line in enumerate(code_lines_new):
            move_cursor(base_row + i, 5)
            print(line + "  ")

        positions = [(base_row + i, 15 + char_idx + 1) for i in range(5)]
        show_multi_cursors(2, positions)  # Beam cursor
        time.sleep(0.15)

    move_cursor(base_row + len(code_lines) + 8, 3)
    print(f"{GREEN}'user' → 'person' に一括変更完了！{RESET}")

    move_cursor(base_row + len(code_lines) + 10, 3)
    input(f"{DIM}[Enter] 次へ...{RESET}")
    clear_multi_cursors()

def demo_rainbow():
    """複数形状の同時表示"""
    clear_screen()
    print_header()

    print(f"{GREEN}[Demo 5]{RESET} 複数形状の同時表示")
    print()
    print("  異なる形状のカーソルを同時に表示:")
    print()

    base_row = 10

    # グリッドを描画
    draw_box(base_row - 1, 3, 45, 8, "Cursor Grid", MAGENTA)

    labels = ["Block", "Beam", "Under"]
    for i, label in enumerate(labels):
        move_cursor(base_row + i * 2, 6)
        print(f"{YELLOW}{label:10s}{RESET}│ ", end="")
        for j in range(5):
            print(f"  ·  ", end="")
        print()

    move_cursor(base_row + 7, 3)
    input(f"{DIM}[Enter] カーソルを配置...{RESET}")

    # 各行に異なる形状のカーソルを配置
    for j in range(5):
        show_multi_cursor(1, base_row, 20 + j * 5)      # Block
        show_multi_cursor(2, base_row + 2, 20 + j * 5)  # Beam
        show_multi_cursor(3, base_row + 4, 20 + j * 5)  # Underline
        time.sleep(0.1)

    move_cursor(base_row + 8, 3)
    print(f"{YELLOW}3種類 × 5列 = 15個のカーソルが表示されています{RESET}")

    move_cursor(base_row + 10, 3)
    input(f"{DIM}[Enter] 次へ...{RESET}")
    clear_multi_cursors()

def demo_falling():
    """落下するカーソル"""
    clear_screen()
    print_header()

    print(f"{GREEN}[Demo 6]{RESET} 落下するカーソル (Matrix風)")
    print()

    cols = 60
    rows = 15
    base_row = 8

    # 各列のカーソル位置を追跡
    cursor_rows = [0] * cols
    speeds = [0.5 + (i % 3) * 0.3 for i in range(cols)]

    for frame in range(100):
        positions = []
        for col in range(cols):
            cursor_rows[col] += speeds[col]
            if cursor_rows[col] >= rows:
                cursor_rows[col] = 0

            row = int(cursor_rows[col])
            if (col + frame) % 4 < 2:  # 半分のカーソルだけ表示
                positions.append((base_row + row, 5 + col))

        clear_multi_cursors()
        if positions:
            show_multi_cursors(2, positions)  # Beam shape
        time.sleep(0.03)

    move_cursor(base_row + rows + 2, 3)
    print(f"{GREEN}Matrix風アニメーション完了！{RESET}")

    move_cursor(base_row + rows + 4, 3)
    input(f"{DIM}[Enter] 次へ...{RESET}")
    clear_multi_cursors()

def demo_escape_sequence():
    """エスケープシーケンスの解説"""
    clear_screen()
    print_header()

    print(f"{GREEN}[Demo 7]{RESET} プロトコル仕様")
    print()

    base_row = 9
    draw_box(base_row - 1, 3, 60, 12, "Multiple Cursors Protocol", CYAN)

    move_cursor(base_row, 5)
    print(f"{YELLOW}フォーマット:{RESET} CSI > SHAPE ; COORD_TYPE:Y:X TRAILER")

    move_cursor(base_row + 2, 5)
    print(f"{WHITE}CSI{RESET}         = ESC [ (\\x1b\\x5b)")
    move_cursor(base_row + 3, 5)
    print(f"{WHITE}>{RESET}           = リテラル '>' 文字")
    move_cursor(base_row + 4, 5)
    print(f"{WHITE}SHAPE{RESET}       = 0:なし 1:█ 2:│ 3:_ 29:メイン同期")
    move_cursor(base_row + 5, 5)
    print(f"{WHITE}COORD_TYPE{RESET}  = 2:点座標 4:矩形(クリア用)")
    move_cursor(base_row + 6, 5)
    print(f"{WHITE}Y:X{RESET}         = 行:列 (1-indexed)")
    move_cursor(base_row + 7, 5)
    print(f"{WHITE}TRAILER{RESET}     = スペース + q")

    move_cursor(base_row + 9, 5)
    print(f"{MAGENTA}例: \\e[>1;2:5:10 q{RESET} → 位置(5,10)にブロックカーソル")

    move_cursor(base_row + 13, 3)
    input(f"{DIM}[Enter] 最終デモへ...{RESET}")

def demo_finale():
    """フィナーレ: 全形状で同心円"""
    clear_screen()
    print_header()

    print(f"{GREEN}[Finale]{RESET} 同心円アニメーション")
    print()

    center_row = 15
    center_col = 35

    for frame in range(120):
        positions = []
        for ring in range(4):
            radius = 2 + ring * 2 + (frame % 20) * 0.1
            points = 8 + ring * 4
            for i in range(points):
                angle = frame * 0.05 + (2 * math.pi * i / points)
                x = int(center_col + radius * math.cos(angle) * 2.5)
                y = int(center_row + radius * math.sin(angle))
                if 5 <= y <= 24 and 5 <= x <= 70:
                    positions.append((y, x))

        clear_multi_cursors()
        if positions:
            shape = 1 + (frame // 30) % 3
            show_multi_cursors(shape, positions)
        time.sleep(0.04)

    clear_multi_cursors()

def main():
    term = os.environ.get("TERM", "")
    if "kitty" not in term and os.environ.get("KITTY_WINDOW_ID") is None:
        print(f"{RED}警告: このデモはkitty 0.43+で実行してください{RESET}")
        print(f"{DIM}(他のターミナルでは複数カーソルが表示されません){RESET}")
        print()
        input("[Enter] で続行...")

    try:
        print_header()

        print("このデモでは kitty 0.43 で追加された")
        print("Multiple Cursors Protocol を紹介します。")
        print()
        print(f"{CYAN}デモ内容:{RESET}")
        print("  1. カーソル形状一覧")
        print("  2. 波形パターン")
        print("  3. スパイラルパターン")
        print("  4. コード編集シミュレーション")
        print("  5. 複数形状の同時表示")
        print("  6. 落下するカーソル (Matrix風)")
        print("  7. プロトコル仕様")
        print("  8. フィナーレ")
        print()

        input(f"{DIM}[Enter] デモ開始...{RESET}")

        demo_intro()
        demo_wave()
        demo_spiral()
        demo_code_editing()
        demo_rainbow()
        demo_falling()
        demo_escape_sequence()
        demo_finale()

        clear_screen()
        print_header()
        print(f"{GREEN}✨ デモ完了{RESET}")
        print()
        print("Multiple Cursors Protocol により、")
        print("ターミナルベースのエディタもGUIエディタと")
        print("同等のマルチカーソル体験を提供できます。")
        print()
        print(f"詳細: {CYAN}https://sw.kovidgoyal.net/kitty/multiple-cursors-protocol/{RESET}")
        print()

    finally:
        clear_multi_cursors()

if __name__ == "__main__":
    main()
