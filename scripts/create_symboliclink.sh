# -n: シンボリックリンクを辿らない（既存リンクがある場合の循環防止）
ln -sfn $(pwd)/.config/nvim ~/.config/nvim
ln -sfn $(pwd)/.config/nvim ~/.vim
ln -sfn $(pwd)/.config/wezterm ~/.config/wezterm
ln -sfn $(pwd)/.config/kitty ~/.config/kitty
ln -sfn $(pwd)/.config/lazygit ~/.config/lazygit
ln -sfn $(pwd)/.config/starship.toml ~/.config/starship.toml
ln -sfn $(pwd)/.tmux.conf ~/.tmux.conf
ln -sfn $(pwd)/.config/alacritty ~/.config/alacritty
ln -sfn $(pwd)/.pyrightconfig.json ~/.pyrightconfig.json
ln -sfn $(pwd)/.config/yazi ~/.config/yazi
ln -sfn $(pwd)/.config/common ~/.config/common

# Claude Code
mkdir -p ~/.claude
ln -sfn $(pwd)/.claude/CLAUDE.md ~/.claude/CLAUDE.md
ln -sfn $(pwd)/.claude/settings.json ~/.claude/settings.json
ln -sfn $(pwd)/.claude/scripts ~/.claude/scripts
ln -sfn $(pwd)/.claude/commands ~/.claude/commands
ln -sfn $(pwd)/.claude/agents ~/.claude/agents
ln -sfn $(pwd)/.claude/skills ~/.claude/skills
