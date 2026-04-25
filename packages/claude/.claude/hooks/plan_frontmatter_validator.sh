#!/bin/bash
# Claude Code PostToolUse hook: プランファイルフロントマター検証
# plans/ディレクトリ内の.mdファイル操作時にフロントマターを検証する
# exit 0 = pass, exit 1 = warn (additionalContext), exit 2 = block (decision: block)
#
# Phase 3-B 拡張 (2026-04-18): 新必須フィールド検証・flow_status enum・
#   review_process.mode:skip warning・必須本文セクション・flow_status:done 未チェック検出
#   いずれも当面は exit 1 警告のみ。既存の exit 2 厳格チェックは変更しない。

set -euo pipefail

input=$(cat)

if ! command -v jq &> /dev/null; then
  exit 0
fi

file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')
[[ -z "$file_path" ]] && exit 0
[[ ! "$file_path" =~ \.claude/plans/.*\.md$ ]] && exit 0

# archive/ 配下は検証スキップ
[[ "$file_path" =~ \.claude/plans/archive/ ]] && exit 0

if [[ -f "$file_path" ]]; then
  content=$(cat "$file_path")
else
  content=$(echo "$input" | jq -r '.tool_input.content // ""')
  [[ -z "$content" ]] && exit 0
fi

filename=$(basename "$file_path")

# ===== 既存: ファイル名検証 (exit 2) =====
if [[ ! "$filename" =~ ^[0-9]{8}-[a-z]+-[a-z0-9-]+\.md$ ]]; then
  echo "{\"decision\":\"block\",\"reason\":\"ERROR: ファイル名が命名規則に違反 / WHY: プランの検索・整理にファイル名の一貫性が必要 / FIX: YYYYMMDD-{genre}-{name}.md 形式にリネーム (例: 20260209-coding-auth-login.md)\"}" >&2
  exit 2
fi

# ===== 既存: フロントマター存在確認 (exit 2) =====
# YAML 仕様: 最初の行が「---」のみの行であることを確認する。
# macOS bash の =~ は文字列全体に対するマッチのため、先頭行を明示的に抽出して比較する。
first_line=$(printf '%s' "$content" | awk 'NR==1{print; exit}')
if [[ "$first_line" != "---" ]]; then
  echo "{\"decision\":\"block\",\"reason\":\"ERROR: フロントマターがない / WHY: プランのステータス管理に必須 / FIX: ファイル先頭に --- で囲んだフロントマターを追加 (status, genre, branch, created, updated)\"}" >&2
  exit 2
fi

# フロントマター抽出
# awk で 1行目の「---」以降・次の「---」の前までを確実に抽出する。
# sed の /^---$/,/^---$/p は閉じ「---」を含んでしまう問題を回避。
frontmatter=$(printf '%s\n' "$content" | awk '
  NR == 1 && /^---$/ { in_fm=1; next }
  in_fm && /^---$/ { exit }
  in_fm { print }
')

# フロントマター値抽出ヘルパー
# \r および trailing whitespace を除去し、CRLF・スペース混入を防ぐ。
extract_fm_value() {
  local field="$1"
  printf '%s\n' "$frontmatter" \
    | awk -v f="^${field}:" '$0 ~ f { sub(/^[^:]+:[[:space:]]*/, ""); print; exit }' \
    | tr -d '\r' \
    | sed -E 's/[[:space:]]+$//'
}

# ===== 既存: 必須フィールド検証 (exit 2) =====
required_fields=("status" "genre" "branch" "created" "updated")
missing_fields=()
for field in "${required_fields[@]}"; do
  if ! printf '%s\n' "$frontmatter" | grep -qE "^${field}:"; then
    missing_fields+=("$field")
  fi
done

if [[ ${#missing_fields[@]} -gt 0 ]]; then
  echo "{\"decision\":\"block\",\"reason\":\"ERROR: 必須フィールド不足 [${missing_fields[*]}] / WHY: プラン管理に必要 / FIX: フロントマターに ${missing_fields[*]} を追加\"}" >&2
  exit 2
fi

# ===== 既存: status 値検証 (exit 2) ※`reviewing` を enum に追加 =====
status=$(extract_fm_value "status")
valid_statuses=("draft" "in_progress" "reviewing" "ready" "testing" "done" "archived")
status_valid=false
for valid in "${valid_statuses[@]}"; do
  [[ "$status" == "$valid" ]] && status_valid=true && break
done

if [[ "$status_valid" == "false" ]]; then
  echo "{\"decision\":\"block\",\"reason\":\"ERROR: 無効なstatus値 '$status' / WHY: ワークフロー管理に必要 / FIX: draft, in_progress, reviewing, ready, testing, done, archived のいずれかを指定\"}" >&2
  exit 2
fi

# ===== 既存: genre 値検証 (exit 2) =====
genre=$(extract_fm_value "genre")
valid_genres=("coding" "bugfix" "spike" "refactoring" "review" "ui-verification" "po-work")
genre_valid=false
for valid in "${valid_genres[@]}"; do
  [[ "$genre" == "$valid" ]] && genre_valid=true && break
done

if [[ "$genre_valid" == "false" ]]; then
  echo "{\"decision\":\"block\",\"reason\":\"ERROR: 無効なgenre値 '$genre' / WHY: ワークフローテンプレート選定に必要 / FIX: coding, bugfix, spike, refactoring, review, ui-verification, po-work のいずれかを指定\"}" >&2
  exit 2
fi

# ===== 既存: 日付形式検証 (exit 2) =====
for field in created updated; do
  value=$(extract_fm_value "$field")
  if [[ ! "$value" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "{\"decision\":\"block\",\"reason\":\"ERROR: ${field}の日付形式が不正 '$value' / WHY: 日付でのソート・検索に必要 / FIX: YYYY-MM-DD 形式 (例: 2026-03-20)\"}" >&2
    exit 2
  fi
done

# ===== 既存: learnings 強制 (status: done, exit 2) =====
# 注意: status: done (exit 2) と flow_status: done (exit 1 警告) で厳格度が異なる。
# 段階的導入方針（plan 3-B: 当面 exit 1 警告）により意図的な非対称。
# Week2 で flow_status 系も exit 2 に昇格予定。
if [[ "$status" == "done" ]]; then
  learnings=$(extract_fm_value "learnings")
  if [[ -z "$learnings" || "$learnings" == "[]" ]]; then
    echo "{\"decision\":\"block\",\"reason\":\"ERROR: status: done だが learnings が空 / WHY: 知見なしでの完了は禁止。同じ問題の再発を防ぐ / FIX: learnings フィールドに記録を追加 (例: learnings: [worktree-ports-troubleshoot])\"}" >&2
    exit 2
  fi
fi

# ===== ここから Phase 3-B 拡張（当面は exit 1 警告のみ） =====

warnings=()

# --- 新必須フィールド検証（top-level key 存在のみ、構造は検証しない） ---
new_required_fields=("flow_status" "team" "output_targets" "review_process")
new_missing=()
for field in "${new_required_fields[@]}"; do
  if ! printf '%s\n' "$frontmatter" | grep -qE "^${field}:"; then
    new_missing+=("$field")
  fi
done
if [[ ${#new_missing[@]} -gt 0 ]]; then
  warnings+=("新必須フィールド不足 [${new_missing[*]}]: scripts/migrate-plans-schema.sh で補完可 / FIX: plan テンプレ (~/.claude/templates/plans/) 参照")
fi

# --- flow_status enum 検証 ---
flow_status=""
if printf '%s\n' "$frontmatter" | grep -qE '^flow_status:'; then
  flow_status=$(extract_fm_value "flow_status")
  valid_flow=("planning" "discovery" "implementing" "reviewing" "verifying" "done")
  flow_valid=false
  for v in "${valid_flow[@]}"; do
    [[ "$flow_status" == "$v" ]] && flow_valid=true && break
  done
  if [[ "$flow_valid" == "false" ]]; then
    warnings+=("flow_status '$flow_status' が無効 / FIX: planning|discovery|implementing|reviewing|verifying|done のいずれか")
  fi
fi

# --- review_process.mode: skip → 警告 ---
rp_mode=$(printf '%s\n' "$frontmatter" | awk '
  /^review_process:/ {in_rp=1; next}
  in_rp && /^[^[:space:]#]/ {in_rp=0}
  in_rp && /^[[:space:]]+mode:/ {
    sub(/^[[:space:]]+mode:[[:space:]]*/, "")
    # インラインコメント除去
    sub(/[[:space:]]*#.*/, "")
    print
    exit
  }
' | tr -d '\r' | sed -E 's/[[:space:]]+$//')
if [[ "$rp_mode" == "skip" ]]; then
  warnings+=("review_process.mode: skip に設定されている / WHY: レビュープロセスが無効化されている / FIX: 意図的でない場合は dual_parallel 等に変更")
fi

# --- 必須本文セクション検証（当面 exit 1 のまま、Phase 4/5 で精緻化） ---
# セクション名は「## Xxx」で始まる行頭一致。固定文字列マッチ + 行末チェックを分離し、
# 正規表現特殊文字の混入（スペース等）による誤マッチを避ける。
required_sections=("## Context" "## Workflow" "## Team Composition" "## Output Targets" "## Review Process" "## チェックポイント")
missing_sections=()
for section in "${required_sections[@]}"; do
  # 完全一致（行末）または「section 」で始まる行のどちらかが存在すれば OK
  if ! printf '%s\n' "$content" | awk -v s="$section" '$0 == s || index($0, s " ") == 1 { f=1; exit } END { exit !f }'; then
    missing_sections+=("$section")
  fi
done
if [[ ${#missing_sections[@]} -gt 0 ]]; then
  warnings+=("必須本文セクション欠落 [${missing_sections[*]}] / FIX: plan テンプレ (~/.claude/templates/plans/_base.md) 参照")
fi

# --- flow_status: done 時の未チェックボックス残存検出 ---
# 注意: status: done (exit 2) と flow_status: done (exit 1 警告) で厳格度が異なる。
# 段階的導入方針（plan 3-B: 当面 exit 1 警告）により意図的な非対称。
# Week2 で flow_status 系も exit 2 に昇格予定。
if [[ "$flow_status" == "done" ]]; then
  # grep -c は 0 件でも "0" を stdout に出力して exit 1 を返すため || true で握りつぶす。
  # set -e 環境で失敗扱いにならないよう || true が必要。tr で \r を除去して算術比較を安全にする。
  unchecked=$(printf '%s\n' "$content" | grep -cE '^[[:space:]]*- \[ \]' | tr -d '\r' || true)
  unchecked="${unchecked:-0}"
  if [[ "$unchecked" -gt 0 ]]; then
    warnings+=("flow_status: done だが未チェック '- [ ]' が ${unchecked} 件残存 / FIX: 全てを '- [x]' に更新、または flow_status を下げる")
  fi
fi

# ===== Phase 3-B-1 拡張: Phase Dashboard 同期検証（exit 1 警告のみ） =====
# plan 冒頭の `## Phase Dashboard` テーブルと本文 `## Phase N:` 見出し、
# `## チェックポイント` 節の対応サブ節の整合を検証する。
# Dashboard 節がない plan は検証スキップ（後方互換）。

# ダッシュボード行抽出（| Phase ... | ... | ... | ... |）
# ヘッダ行（| Phase | 状態 | ...|）と区切り行（|---|...|）は `^\| *Phase -?[0-9]+` で除外
# M3 (Claude): Dashboard 節終了を exit → in_dash=0 に統一（フォールスルー対策）
dashboard_rows=$(printf '%s\n' "$content" | awk '
  /^## Phase Dashboard[[:space:]]*$/ { in_dash=1; next }
  in_dash && /^## / && !/^## Phase Dashboard[[:space:]]*$/ { in_dash=0 }
  in_dash && /^\|[[:space:]]*Phase[[:space:]]+-?[0-9]+/ { print }
')

if [[ -n "$dashboard_rows" ]]; then
  # 1. Phase 数の一致
  dashboard_phase_count=$(printf '%s\n' "$dashboard_rows" | grep -c '^|' || true)
  dashboard_phase_count="${dashboard_phase_count:-0}"

  # 本文 `^## Phase N:` 見出し数。
  # ## チェックポイント / ## 検証方法 節配下の `### Phase N` は除外（そもそも h3 なのでマッチしない）。
  # また Dashboard 節内部を誤って数えないよう in_dash で除外。
  # M1 (Claude): Dashboard 見出しの終了条件を `!/^## Phase Dashboard[[:space:]]*$/` に強化（サブ見出し誤反応防止）
  body_phase_count=$(printf '%s\n' "$content" | awk '
    /^## Phase Dashboard[[:space:]]*$/ { in_dash=1; next }
    in_dash && /^## / && !/^## Phase Dashboard[[:space:]]*$/ { in_dash=0 }
    !in_dash && /^## Phase -?[0-9]+:/ { count++ }
    END { print count+0 }
  ')

  if [[ "$dashboard_phase_count" -ne "$body_phase_count" ]]; then
    warnings+=("Dashboard Phase 数 (${dashboard_phase_count}) と本文 '## Phase N:' 見出し数 (${body_phase_count}) が不一致 / FIX: どちらかを揃える")
  fi

  # 各ダッシュボード行の状態記号・承認値・レビューiter を検証
  invalid_symbols=()
  invalid_approvals=()
  empty_iters=()
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    # | Phase X: 名前 | [?] | iter | 承認 |
    phase_label=$(printf '%s\n' "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}')
    status_sym=$(printf '%s\n' "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3}')
    review_iter=$(printf '%s\n' "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $4); print $4}')
    approval=$(printf '%s\n' "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $5); print $5}')
    phase_id=$(printf '%s\n' "$phase_label" | grep -oE 'Phase -?[0-9]+' | head -1 || true)

    # 状態記号 enum
    case "$status_sym" in
      '[ ]'|'[~]'|'[r]'|'[x]') ;;
      *) invalid_symbols+=("${phase_id:-?}='$status_sym'") ;;
    esac

    # 承認値 enum
    case "$approval" in
      pending|approved|changes_requested|-) ;;
      *) invalid_approvals+=("${phase_id:-?}='$approval'") ;;
    esac

    # レビューiter 非空
    if [[ -z "$review_iter" ]]; then
      empty_iters+=("${phase_id:-?}")
    fi
  done <<< "$dashboard_rows"

  if [[ ${#invalid_symbols[@]} -gt 0 ]]; then
    warnings+=("Dashboard 状態記号が無効: ${invalid_symbols[*]} / FIX: [ ]|[~]|[r]|[x] のいずれか")
  fi
  if [[ ${#invalid_approvals[@]} -gt 0 ]]; then
    warnings+=("Dashboard 承認値が無効: ${invalid_approvals[*]} / FIX: pending|approved|changes_requested|- のいずれか")
  fi
  if [[ ${#empty_iters[@]} -gt 0 ]]; then
    warnings+=("Dashboard レビューiter 列が空: ${empty_iters[*]} / FIX: '-' または iter-N done 等で埋める")
  fi

  # flow_status 整合性（frontmatter の flow_status が有効な場合のみ）
  if [[ -n "$flow_status" ]]; then
    all_symbols=$(printf '%s\n' "$dashboard_rows" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3}')
    has_x=$(printf '%s\n' "$all_symbols" | grep -c '^\[x\]$' || true)
    has_tilde=$(printf '%s\n' "$all_symbols" | grep -c '^\[~\]$' || true)
    has_r=$(printf '%s\n' "$all_symbols" | grep -c '^\[r\]$' || true)
    has_x="${has_x:-0}"
    has_tilde="${has_tilde:-0}"
    has_r="${has_r:-0}"

    case "$flow_status" in
      done)
        if [[ "$has_x" -lt "$dashboard_phase_count" ]]; then
          warnings+=("flow_status: done だが Dashboard に [x] 以外の Phase が残存 / FIX: 全 Phase を [x] に、または flow_status を下げる")
        fi
        ;;
      implementing)
        if [[ "$((has_tilde + has_x))" -lt 1 ]]; then
          warnings+=("flow_status: implementing だが Dashboard に [~] も [x] もない / FIX: 着手中 Phase を [~] に")
        fi
        ;;
      reviewing)
        if [[ "$((has_r + has_x))" -lt 1 ]]; then
          warnings+=("flow_status: reviewing だが Dashboard に [r] も [x] もない / FIX: レビュー中 Phase を [r] に")
        fi
        ;;
      verifying)
        if [[ "$has_x" -lt 1 ]]; then
          warnings+=("flow_status: verifying だが Dashboard に [x] がない / FIX: 少なくとも 1 Phase を [x] に")
        fi
        ;;
      planning|discovery)
        # 制約なし
        ;;
    esac
  fi

  # 完了整合性: [x] approved Phase は、チェックポイント節の対応サブ節の全 [ ] が [x]
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    status_sym=$(printf '%s\n' "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3}')
    approval=$(printf '%s\n' "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $5); print $5}')
    phase_label=$(printf '%s\n' "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}')
    # Claude M-NEW-1 (iter-2): `grep -oE -- '-?[0-9]+'` は ERE 実装により `Phase -1` から
    # `-1` を返すか `1` を返すかが不確定。sed で `Phase ` プレフィックスを剥がして
    # 残りを数値文字列として扱う方が安全。
    phase_num=$(printf '%s\n' "$phase_label" | grep -oE 'Phase -?[0-9]+' | head -1 | sed -E 's/^Phase[[:space:]]+//' || true)

    if [[ "$status_sym" == "[x]" ]] && [[ "$approval" == "approved" ]] && [[ -n "$phase_num" ]]; then
      unchecked_in_phase=$(printf '%s\n' "$content" | awk -v pnum="$phase_num" '
        /^## チェックポイント/ { in_check=1; next }
        # M-2 (Codex): チェックポイント終了条件を簡素化（## チェックポイント行は既に next されているため除外不要）
        in_check && /^## / { in_check=0 }
        # M-1 (Codex): サブフェーズ記法 `### Phase 3-B-0` 等は主 Phase の集計対象外
        # `-[A-Za-z]` が続く場合はサブフェーズとして in_phase をリセットしスキップ
        in_check && /^### Phase -?[0-9]+-[A-Za-z]/ { in_phase=0; next }
        # 主 Phase 見出し: 数字の直後が `-` または別の数字でない場合のみマッチ
        in_check && /^### Phase -?[0-9]+([^-0-9].*|$)/ {
          match($0, /-?[0-9]+/)
          cur_pnum = substr($0, RSTART, RLENGTH)
          in_phase = (cur_pnum == pnum) ? 1 : 0
          next
        }
        in_check && in_phase && /^[[:space:]]*- \[ \]/ { count++ }
        END { print count+0 }
      ')
      if [[ "${unchecked_in_phase:-0}" -gt 0 ]]; then
        warnings+=("Phase ${phase_num} は [x] approved だがチェックポイント節に未チェック '- [ ]' が ${unchecked_in_phase} 件 / FIX: 全て [x] に、またはダッシュボード側を戻す")
      fi
    fi
  done <<< "$dashboard_rows"
fi

# --- 既存: ファイル名genre と frontmatter genre の整合性（warnings に統合） ---
# ファイル名は YYYYMMDD-{genre}-{name}.md 形式。{genre} には ui-verification/po-work など
# ハイフン付きの値もあるため、valid_genres に対してプレフィックスマッチで決定論的に抽出する。
filename_body="${filename#????????-}"
filename_genre=""
for valid in "${valid_genres[@]}"; do
  if [[ "$filename_body" == "$valid"-* ]]; then
    filename_genre="$valid"
    break
  fi
done
if [[ -z "$filename_genre" ]]; then
  warnings+=("ファイル名から genre を判定できない / FIX: YYYYMMDD-{genre}-{name}.md 形式で {genre} を valid_genres のいずれかに")
elif [[ "$filename_genre" != "$genre" ]]; then
  warnings+=("ファイル名genre '$filename_genre' とfrontmatter genre '$genre' が不一致 / FIX: ファイル名か frontmatter を揃える")
fi

# ===== warnings 統合出力（exit 1） =====
if [[ ${#warnings[@]} -gt 0 ]]; then
  joined=$(printf -- '- %s\n' "${warnings[@]}")
  message=$(printf 'WARNING: plan frontmatter / 本文チェックに以下の指摘があります（段階的導入中の exit 1 警告、ブロックはしません）:\n%s' "$joined")
  jq -n --arg m "$message" '{additionalContext: $m}'
  exit 1
fi

exit 0
