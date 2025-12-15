#!/usr/bin/env python3
"""
Graphics Protocol Demo
======================
kitty Graphics Protocol を使ってターミナルに画像を表示するデモ

参考: https://sw.kovidgoyal.net/kitty/graphics-protocol/

使用方法:
    python graphics_demo.py              # 全デモを実行
    python graphics_demo.py inline       # インライン画像のみ
    python graphics_demo.py animation    # アニメーションのみ
    python graphics_demo.py chart        # チャート生成
"""

import sys
import os
import base64
import zlib
import tempfile
from io import BytesIO

# ANSI色
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def print_header(title: str):
    """ヘッダーを表示"""
    print(f"\n{CYAN}{'━' * 60}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'━' * 60}{RESET}\n")


def press_enter():
    """Enter待ち"""
    print(f"\n{YELLOW}[Enter]で続行...{RESET}")
    input()


def display_image_kitty(data: bytes, width: int = 0, height: int = 0):
    """kitty Graphics Protocol で画像を表示"""
    # 画像データをbase64エンコード
    b64_data = base64.standard_b64encode(data).decode('ascii')

    # チャンクに分割して送信
    chunk_size = 4096

    # 最初のチャンク
    first_chunk = b64_data[:chunk_size]
    remaining = b64_data[chunk_size:]

    # 画像送信開始
    if remaining:
        # 複数チャンクの場合
        sys.stdout.write(f'\033_Ga=T,f=100,m=1;{first_chunk}\033\\')
        sys.stdout.flush()

        # 中間チャンク
        while len(remaining) > chunk_size:
            chunk = remaining[:chunk_size]
            remaining = remaining[chunk_size:]
            sys.stdout.write(f'\033_Gm=1;{chunk}\033\\')
            sys.stdout.flush()

        # 最後のチャンク
        sys.stdout.write(f'\033_Gm=0;{remaining}\033\\')
        sys.stdout.flush()
    else:
        # 単一チャンク
        sys.stdout.write(f'\033_Ga=T,f=100;{first_chunk}\033\\')
        sys.stdout.flush()

    print()


def create_gradient_png(width: int = 200, height: int = 100) -> bytes:
    """シンプルなグラデーション画像をPNGで生成"""
    try:
        from PIL import Image
        import io

        img = Image.new('RGB', (width, height))
        pixels = img.load()

        for x in range(width):
            for y in range(height):
                r = int(255 * x / width)
                g = int(255 * y / height)
                b = 128
                pixels[x, y] = (r, g, b)

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    except ImportError:
        return None


def demo_inline_image():
    """インライン画像のデモ"""
    print_header("Demo 1: インライン画像表示")

    print("kitty Graphics Protocol を使うと、ターミナルに画像を直接表示できます。")
    print("")
    print("従来のターミナル: テキストのみ")
    print("kitty: 画像、グラフ、チャートなどをインライン表示")
    print("")

    # kitten icat を使用
    print(f"{GREEN}kitten icat コマンドで画像を表示:{RESET}")
    print("")

    # サンプル画像を探す
    sample_paths = [
        "/usr/share/pixmaps/kitty.png",
        "/usr/share/icons/hicolor/256x256/apps/kitty.png",
        "/usr/share/backgrounds/",
    ]

    image_found = False
    for path in sample_paths:
        if os.path.exists(path):
            if os.path.isfile(path):
                print(f"  画像: {path}")
                os.system(f"kitten icat --align left {path}")
                image_found = True
                break
            elif os.path.isdir(path):
                for f in os.listdir(path):
                    if f.endswith(('.png', '.jpg', '.jpeg')):
                        full_path = os.path.join(path, f)
                        print(f"  画像: {full_path}")
                        os.system(f"kitten icat --align left --scale-up {full_path}")
                        image_found = True
                        break
        if image_found:
            break

    if not image_found:
        # Pillowで画像を生成
        print("システム画像が見つからないため、動的に生成します...")
        png_data = create_gradient_png()
        if png_data:
            display_image_kitty(png_data)
        else:
            print(f"{YELLOW}Pillow がインストールされていないため、画像を生成できません{RESET}")
            print("インストール: pip install Pillow")


def demo_unicode_placeholder():
    """Unicode placeholderのデモ"""
    print_header("Demo 2: Unicode Placeholder")

    print("kittyでは、画像をUnicode placeholderとして配置できます。")
    print("これにより、テキストと画像を自然に混在させられます。")
    print("")
    print("例: ダッシュボードでグラフをインライン表示")
    print("例: ログビューアでエラー箇所をハイライト画像で表示")
    print("")

    # kitten icatの--placeオプション
    print(f"{GREEN}配置指定の例:{RESET}")
    print("  kitten icat --place 20x10@5x3 image.png")
    print("  → 幅20、高さ10セルの位置(5,3)に画像を配置")


def demo_animation():
    """アニメーションのデモ"""
    print_header("Demo 3: アニメーション")

    print("Graphics Protocol はアニメーションGIFもサポートします。")
    print("")

    # 簡易アニメーション（テキストベース）
    import time

    frames = [
        "  ●○○○○  ",
        "  ○●○○○  ",
        "  ○○●○○  ",
        "  ○○○●○  ",
        "  ○○○○●  ",
        "  ○○○●○  ",
        "  ○○●○○  ",
        "  ○●○○○  ",
    ]

    print("簡易アニメーション (テキストベース):")
    print("")

    for _ in range(2):
        for frame in frames:
            sys.stdout.write(f"\r  {GREEN}{frame}{RESET}")
            sys.stdout.flush()
            time.sleep(0.1)

    print("\n")
    print("実際のGIFアニメーション:")
    print("  kitten icat animation.gif")


def demo_protocol_explanation():
    """プロトコルの説明"""
    print_header("Graphics Protocol の仕組み")

    print("kitty Graphics Protocol は以下の機能を提供します:")
    print("")
    print(f"  {GREEN}[1]{RESET} 画像データの送信 (PNG, JPEG, GIF)")
    print(f"  {GREEN}[2]{RESET} 画像の配置・サイズ指定")
    print(f"  {GREEN}[3]{RESET} アニメーション制御")
    print(f"  {GREEN}[4]{RESET} 透過・合成")
    print(f"  {GREEN}[5]{RESET} 画像の削除・更新")
    print("")
    print("エスケープシーケンス形式:")
    print(f"  {YELLOW}ESC_G<control data>;<payload>ESC\\{RESET}")
    print("")
    print("対応アプリケーション:")
    print("  - ranger (ファイルマネージャ)")
    print("  - viu (画像ビューア)")
    print("  - matplotlib (kitty backend)")
    print("  - neovim (画像プラグイン)")
    print("")
    print(f"参考: {CYAN}https://sw.kovidgoyal.net/kitty/graphics-protocol/{RESET}")


def demo_matplotlib():
    """matplotlibでのグラフ表示"""
    print_header("Demo 4: matplotlib グラフ")

    print("matplotlib を kitty バックエンドで使うと、")
    print("グラフをターミナルに直接表示できます。")
    print("")

    try:
        import matplotlib
        matplotlib.use('module://matplotlib-backend-kitty')
        import matplotlib.pyplot as plt
        import numpy as np

        # サンプルグラフ
        x = np.linspace(0, 10, 100)
        y = np.sin(x)

        plt.figure(figsize=(6, 3))
        plt.plot(x, y)
        plt.title('Sin Wave')
        plt.xlabel('x')
        plt.ylabel('sin(x)')
        plt.show()

    except ImportError as e:
        print(f"{YELLOW}matplotlib-backend-kitty がインストールされていません{RESET}")
        print("")
        print("インストール方法:")
        print("  pip install matplotlib-backend-kitty")
        print("")
        print("使用方法:")
        print("  import matplotlib")
        print("  matplotlib.use('module://matplotlib-backend-kitty')")
        print("  import matplotlib.pyplot as plt")
        print("  plt.plot([1, 2, 3], [1, 4, 9])")
        print("  plt.show()")


def main():
    """メイン"""
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command == "inline":
        demo_inline_image()
    elif command == "animation":
        demo_animation()
    elif command == "chart":
        demo_matplotlib()
    elif command == "protocol":
        demo_protocol_explanation()
    elif command == "all":
        print_header("kitty Graphics Protocol Demo")
        print("このデモでは、kittyの Graphics Protocol を使った")
        print("画像表示機能を紹介します。")
        print("")
        print("従来のターミナルは「テキストのみ」でしたが、")
        print("kittyはプロトコルレベルで画像をサポートします。")
        press_enter()

        demo_protocol_explanation()
        press_enter()

        demo_inline_image()
        press_enter()

        demo_unicode_placeholder()
        press_enter()

        demo_animation()
        press_enter()

        demo_matplotlib()

        print_header("Demo Complete!")
        print("Graphics Protocol により、ターミナルは")
        print("「テキストのみ」という制約から解放されます。")
        print("")
        print("これは tmux では実現できない kitty の強みの一つです。")
    else:
        print(f"Usage: {sys.argv[0]} [inline|animation|chart|protocol|all]")
        sys.exit(1)


if __name__ == "__main__":
    main()
