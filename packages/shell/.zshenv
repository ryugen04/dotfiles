# .zshenv - 非対話シェルでも読み込まれる設定
# lazygitなどのサブプロセスでもPATHが通るようにする

# Cargo
[[ -f "$HOME/.cargo/env" ]] && . "$HOME/.cargo/env"

# nodenv shims
export PATH="$HOME/.nodenv/shims:$PATH"
