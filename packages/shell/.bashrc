# .bashrc - bash エントリポイント

# 非対話シェルでは終了
[[ $- != *i* ]] && return

# bash 固有設定
shopt -s histappend
shopt -s checkwinsize
HISTSIZE=10000
HISTFILESIZE=20000
HISTCONTROL=ignoreboth

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

# bash 補完
if ! shopt -oq posix; then
    if [[ -f /usr/share/bash-completion/bash_completion ]]; then
        source /usr/share/bash-completion/bash_completion
    elif [[ -f /etc/bash_completion ]]; then
        source /etc/bash_completion
    fi
fi

# zoxide（最後に初期化）
command -v zoxide &>/dev/null && eval "$(zoxide init bash)"
