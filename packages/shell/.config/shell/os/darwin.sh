# os/darwin.sh - macOS 固有設定

# Homebrew
if [[ -d /opt/homebrew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -d /usr/local/Homebrew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi

# macOS には pbcopy/pbpaste がデフォルトで存在するため設定不要
