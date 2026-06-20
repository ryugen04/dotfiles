# PDF → Markdown 変換ルール（絶対遵守）

NO MANUAL PDF TRANSCRIPTION - USE MARKER-PDF

## 原則

**PDFをMarkdownに変換する際は、Read ツールで直接読み取って手作業で変換してはならない。必ず marker-pdf を使用する。**

## 理由

- marker-pdf は GPU を活用した高精度 OCR で、表・図・レイアウトを正確に保持する
- 手作業変換は時間がかかり、誤りが混入しやすい
- 大きな PDF は 10 ページごとに分割処理することで効率とメモリ使用量を最適化

## 必須手順

### 1. PDF のダウンロード

WebFetch でダウンロードされた PDF のパスを確認する。

### 2. marker-pdf でバッチ変換

10 ページごとに分割して変換する:

```bash
# ページ 0-9
uvx --from marker-pdf marker_single "<pdf_path>" --output_dir /tmp/output-p0 --page_range "0-9"

# ページ 10-19
uvx --from marker-pdf marker_single "<pdf_path>" --output_dir /tmp/output-p10 --page_range "10-19"

# ... 以降同様に続ける
```

### 3. 結果の結合

```bash
cat /tmp/output-p0/*/*.md /tmp/output-p10/*/*.md ... > /tmp/combined.md
```

### 4. 配置

変換した Markdown をプロジェクトの適切な場所に配置:

| 用途 | 配置先 |
|------|--------|
| ドメイン知識（レセプト関連） | `workspace/.claude/docs/domain/receipt/` |
| ドメイン知識（その他） | `workspace/.claude/docs/domain/{category}/` |
| 参考資料 | `.claude/docs/reference/` |

## オプション

| オプション | 用途 |
|-----------|------|
| `--disable_image_extraction` | 画像抽出を無効化（テキストのみ必要な場合） |
| `--output_format json` | JSON 形式で出力（プログラム処理用） |
| `--disable_ocr` | OCR を無効化（埋め込みテキストのみ） |

## 禁止事項

| 禁止 | 理由 |
|------|------|
| Read ツールで PDF を読んで手作業でまとめる | 低精度・非効率 |
| 全ページを一括変換（50ページ以上） | メモリ枯渇のリスク |
| 変換結果を確認せずに配置 | OCR エラーの見落とし |

## 例外

- 1-2 ページの短い PDF
- テキストが主で表・図がほとんどない場合
- marker-pdf がインストールできない環境（その場合はユーザーに確認）

---

**最終更新**: 2026-06-10
**背景**: PDF の手作業変換による非効率と品質低下を防ぐため
