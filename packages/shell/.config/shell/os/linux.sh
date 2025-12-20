# os/linux.sh - Linux 固有設定

# Java
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# Chrome (Flutter 用)
export CHROME_EXECUTABLE="/usr/bin/google-chrome-stable"

# クリップボード（macOS の pbcopy/pbpaste 互換）
alias pbcopy='xsel --clipboard --input'
alias pbpaste='xsel --clipboard --output'

# IME 設定
export GLFW_IM_MODULE=ibus

# Claude Desktop 設定
export CLAUDE_CONFIG="${HOME}/.config/Claude/claude_desktop_config.json"

# PATH 設定
_add_to_path "/opt/gradle/gradle-7.4.2/bin"
_add_to_path "$HOME/.fvm_flutter/bin"
_add_to_path "$HOME/development/flutter/bin"
_add_to_path "$HOME/bin/yazi"

# Android Studio
alias android-studio='/usr/local/android-studio/bin/studio.sh'

# Ranger
alias ranger='. ranger'
