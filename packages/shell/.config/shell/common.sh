# common.sh - bash/zsh 共通設定

# エイリアス
alias ls='lsd -a --color=auto'
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'

# 安全操作
alias mvi='mv -i'
alias cpi='cp -i'
alias rmi='rm -i'

# エディタ
alias vi='nvim'

# Git
alias gg='lazygit'

# Python
alias python='python3'

# 履歴
alias hist='history 10'
alias histgrep='history | grep'

# プロジェクト
export PROJECTS_DIR="${PROJECTS_DIR:-$HOME/dev/projects}"
export DOTFILES_DIR="${DOTFILES_DIR:-$PROJECTS_DIR/dotfiles}"
alias cdp='cd "$PROJECTS_DIR"'
alias cdpd='cd "$DOTFILES_DIR"'

# Claude
alias yolo='claude --dangerously-skip-permissions'
alias yolor='claude --dangerously-skip-permissions --resume'

alias cx='codex'
alias ch='codex --profile codex-config-edit'
# 環境変数
export LANG=en_US.UTF-8
export EDITOR="nvim"

# 1Password SSH Agent
export SSH_AUTH_SOCK="${HOME}/.1password/agent.sock"

# PATH 設定（重複追加を防ぐ）
_add_to_path() {
    case ":$PATH:" in
        *":$1:"*) ;;
        *) export PATH="$1:$PATH" ;;
    esac
}

_add_to_path "$HOME/.local/bin"
_add_to_path "$HOME/.codex/ai-dlc/bin"
_add_to_path "$HOME/bin"
_add_to_path "$HOME/.yarn/bin"
_add_to_path "$HOME/.pub-cache/bin"

# yazi ディレクトリ変更統合
function y() {
    local tmp cwd
    tmp="$(mktemp -t "yazi-cwd.XXXXXX")"
    yazi "$@" --cwd-file="$tmp"
    if cwd="$(command cat -- "$tmp")" && [[ -n "$cwd" ]] && [[ "$cwd" != "$PWD" ]]; then
        builtin cd -- "$cwd"
    fi
    rm -f -- "$tmp"
}
