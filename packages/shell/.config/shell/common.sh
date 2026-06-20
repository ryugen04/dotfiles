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

alias saw='sango down && sango up --profile full --default-ports'
alias sar='sango down && sango up --profile full'

careflow_sync_workspace() {
  local root="${1:-}"
  if [[ -z "$root" ]]; then
    root="$(command sango root 2>/dev/null)" || return 0
  fi
  [[ -n "$root" ]] || return 0
  [[ -x "$DOTFILES_DIR/install.sh" ]] || return 0
  command "$DOTFILES_DIR/install.sh" workspace-careflow "$root"
}

sango() {
  local sango_status is_create=false is_help=false explicit_root="" expect_root=false
  local previous="" arg root

  for arg in "$@"; do
    if $expect_root; then
      explicit_root="$arg"
      expect_root=false
    fi
    case "$arg" in
      -h|--help) is_help=true ;;
      --root) expect_root=true ;;
      --root=*) explicit_root="${arg#--root=}" ;;
    esac
    if [[ "$previous" == "worktree" && "$arg" == "create" ]]; then
      is_create=true
    fi
    previous="$arg"
  done

  command sango "$@"
  sango_status=$?
  if [[ $sango_status -eq 0 && "$is_create" == true && "$is_help" != true ]]; then
    if [[ -n "$explicit_root" ]]; then
      root="$(command sango --root "$explicit_root" root 2>/dev/null)" || return $sango_status
      careflow_sync_workspace "$root" || return $?
    else
      careflow_sync_workspace || return $?
    fi
  fi
  return $sango_status
}
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
_add_to_path "$HOME/.cargo/bin"
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

difit-current() {
  local upstream base

  upstream="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)"
  base="$(git merge-base "$upstream" HEAD)" || return

  echo "difit: . $base"
  difit . "$base" --include-untracked "$@"
}

alias dip='difit-current'
