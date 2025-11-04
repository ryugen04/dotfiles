
# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Add an "alert" alias for long running commands.  Use like so:
#   sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi


# my setting
# path import
alias ranger='. ranger'
# alias pbcopy='xsel --clipboard --input'
export LANG=en_US.UTF-8
alias vi='nvim'
alias gg='lazygit'
alias python='python3'

# aliases
alias ls='lsd -a --color=auto'
alias ..='cd ..'
alias mvi='mv -i'
alias cpi='cp -i'
alias rmi='rm -i'
alias hist='history 10'
alias histgrep='history | grep $1'

alias cdp='cd ~/dev/projects'
alias cdpd='cd ~/dev/projects/dotfiles'
alias yolo='claude --dangerously-skip-permissions'
alias yolor='claude --dangerously-skip-permissions --resume'

export EDITOR="nvim"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion


eval "$(pyenv init --path)"
eval "$(starship init bash)"
# eval "$(~/.rbenv/bin/rbenv init -)"
# [[ -d ~/.rbenv  ]] && \
#   export PATH=${HOME}/.rbenv/bin:${PATH} && \
#   eval "$(rbenv init -)"
# export PATH="$HOME/development/flutter/bin:$PATH"
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
	yazi "$@" --cwd-file="$tmp"
	if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
		builtin cd -- "$cwd"
	fi
	rm -f -- "$tmp"
}
