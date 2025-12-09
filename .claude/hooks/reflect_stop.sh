#!/usr/bin/env bash
# Stop 用振り返り促進スクリプト
# /exit 等でセッション終了時に、理解が浅いまま終わっていないかを簡潔に問い直す

set -euo pipefail

TODAY=$(date +%Y-%m-%d)
LOG_DIR="$HOME/dev/logs/claude-catchup/dev"

cat <<EOF

[ClaudeCode] セッションを終了します。

今回の作業が次のいずれかに当てはまる場合、
軽く振り返りをしておくと後で困りにくくなります:

- AI エージェントに任せた部分が大きい
- 変更の意図や影響範囲がまだ曖昧
- 同様の問題が今後もまた出てきそう

そう感じる場合は、次のコマンドが役立ちます:

- /catchup:daily : 今日の理解と曖昧な点を整理
- /catchup:test  : 理解度を 5 問で確認

小さな修正であれば、そのまま /exit や /clear で終了して問題ありません。

ログ: $LOG_DIR/$TODAY.yaml に編集履歴が残っています。
EOF

exit 0
