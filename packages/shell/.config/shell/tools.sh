# tools.sh - ツール初期化

# NVM (Node Version Manager)
export NVM_DIR="$HOME/.nvm"
[[ -s "$NVM_DIR/nvm.sh" ]] && source "$NVM_DIR/nvm.sh"
[[ -s "$NVM_DIR/bash_completion" ]] && source "$NVM_DIR/bash_completion"

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
if [[ -d "$PYENV_ROOT" ]]; then
    _add_to_path "$PYENV_ROOT/bin"
    eval "$(pyenv init --path)"
fi

# rbenv
if [[ -d "$HOME/.rbenv" ]]; then
    _add_to_path "$HOME/.rbenv/bin"
    eval "$(rbenv init -)"
fi

# Deno
export DENO_INSTALL="$HOME/.deno"
[[ -d "$DENO_INSTALL" ]] && _add_to_path "$DENO_INSTALL/bin"

# zoxide
if command -v zoxide &>/dev/null; then
    if [[ -n "$BASH_VERSION" ]]; then
        eval "$(zoxide init bash)"
    elif [[ -n "$ZSH_VERSION" ]]; then
        eval "$(zoxide init zsh)"
    fi
fi

# Starship プロンプト（最後に初期化）
if command -v starship &>/dev/null; then
    if [[ -n "$BASH_VERSION" ]]; then
        eval "$(starship init bash)"
    elif [[ -n "$ZSH_VERSION" ]]; then
        eval "$(starship init zsh)"
    fi
fi
