# .zshrc - zsh エントリポイント

# zsh 固有設定
setopt HIST_IGNORE_DUPS
setopt SHARE_HISTORY
setopt AUTO_CD
setopt CORRECT
HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.zsh_history

# シェル設定ディレクトリ
SHELL_CONFIG="${HOME}/.config/shell"

# 共通設定を読み込み
[[ -r "${SHELL_CONFIG}/common.sh" ]] && source "${SHELL_CONFIG}/common.sh"

# OS 固有設定
case "$(uname -s)" in
    Linux)  [[ -r "${SHELL_CONFIG}/os/linux.sh" ]] && source "${SHELL_CONFIG}/os/linux.sh" ;;
    Darwin) [[ -r "${SHELL_CONFIG}/os/darwin.sh" ]] && source "${SHELL_CONFIG}/os/darwin.sh" ;;
esac

# ツール初期化
[[ -r "${SHELL_CONFIG}/tools.sh" ]] && source "${SHELL_CONFIG}/tools.sh"

# ローカル設定（git 管理外、存在する場合のみ）
[[ -r "${SHELL_CONFIG}/local.sh" ]] && source "${SHELL_CONFIG}/local.sh"

# zsh 補完
autoload -Uz compinit && compinit

# zoxide（最後に初期化）
command -v zoxide &>/dev/null && eval "$(zoxide init zsh)"
