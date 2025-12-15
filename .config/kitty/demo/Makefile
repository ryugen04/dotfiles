# =============================================================================
# kitty Protocol-driven Terminal Demo
# =============================================================================
# 使用方法:
#   make demo      - Remote Control デモを実行
#   make multi     - マルチサーバーオーケストレーションをセットアップ
#   make keyboard  - Keyboard Protocol デモを実行
#   make graphics  - Graphics Protocol デモを実行
#   make cursor    - Multiple Cursors Protocol デモを実行
#   make broadcast - Broadcast kitten デモを実行
#   make trail     - Cursor Trail デモを実行
#   make hints     - Hints kitten デモを実行
#   make ssh       - SSH kitten デモを実行
#   make all       - 全デモを順番に実行
#   make clean     - クリーンアップ
# =============================================================================

SHELL := /bin/bash
DEMO_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
LOG_DIR := $(DEMO_DIR)/logs

.PHONY: all demo multi keyboard graphics cursor broadcast trail hints ssh clean help status

# デフォルトターゲット
help:
	@echo ""
	@echo "kitty Protocol-driven Terminal Demo"
	@echo "===================================="
	@echo ""
	@echo "基本デモ:"
	@echo "  make demo      - Remote Control デモを実行"
	@echo "  make multi     - マルチサーバーオーケストレーションをセットアップ"
	@echo "  make keyboard  - Keyboard Protocol デモを実行"
	@echo "  make graphics  - Graphics Protocol デモを実行"
	@echo ""
	@echo "革新的機能デモ:"
	@echo "  make cursor    - Multiple Cursors Protocol デモ (v0.43+)"
	@echo "  make broadcast - Broadcast kitten デモ"
	@echo "  make trail     - Cursor Trail デモ (v0.37+)"
	@echo "  make hints     - Hints kitten デモ"
	@echo "  make ssh       - SSH kitten デモ"
	@echo ""
	@echo "その他:"
	@echo "  make all       - 全デモを順番に実行"
	@echo "  make status    - 現在の状態を表示"
	@echo "  make clean     - クリーンアップ"
	@echo ""

# =============================================================================
# Remote Control Demo
# =============================================================================
demo:
	@echo "Remote Control デモを開始..."
	@$(DEMO_DIR)/rc_demo.sh all

demo-step1:
	@$(DEMO_DIR)/rc_demo.sh 1

demo-step2:
	@$(DEMO_DIR)/rc_demo.sh 2

demo-step3:
	@$(DEMO_DIR)/rc_demo.sh 3

demo-step4:
	@$(DEMO_DIR)/rc_demo.sh 4

demo-step5:
	@$(DEMO_DIR)/rc_demo.sh 5

# =============================================================================
# Multi-Server Orchestration
# =============================================================================
multi: multi-setup multi-start
	@echo ""
	@echo "マルチサーバーセットアップ完了"
	@echo "次のステップ:"
	@echo "  make multi-traffic  # テストトラフィックを生成"
	@echo "  make multi-clean    # クリーンアップ"

multi-setup:
	@echo "4タブ構成をセットアップ..."
	@$(DEMO_DIR)/orchestrate.sh setup

multi-start:
	@echo "サーバーを起動..."
	@$(DEMO_DIR)/orchestrate.sh start

multi-traffic:
	@echo "テストトラフィックを生成..."
	@$(DEMO_DIR)/orchestrate.sh traffic

multi-status:
	@$(DEMO_DIR)/orchestrate.sh status

multi-clean:
	@$(DEMO_DIR)/orchestrate.sh cleanup

# =============================================================================
# Keyboard Protocol Demo
# =============================================================================
keyboard:
	@echo "Keyboard Protocol デモを開始..."
	@if [ -f "$(DEMO_DIR)/keyboard_demo.sh" ]; then \
		$(DEMO_DIR)/keyboard_demo.sh; \
	else \
		echo "keyboard_demo.sh が見つかりません"; \
	fi

# =============================================================================
# Graphics Protocol Demo
# =============================================================================
graphics:
	@echo "Graphics Protocol デモを開始..."
	@if [ -f "$(DEMO_DIR)/graphics_demo.py" ]; then \
		python3 $(DEMO_DIR)/graphics_demo.py; \
	else \
		echo "graphics_demo.py が見つかりません"; \
	fi

# =============================================================================
# Multiple Cursors Protocol Demo (v0.43+)
# =============================================================================
cursor:
	@echo "Multiple Cursors Protocol デモを開始..."
	@if [ -f "$(DEMO_DIR)/multi_cursor_demo.py" ]; then \
		python3 $(DEMO_DIR)/multi_cursor_demo.py; \
	else \
		echo "multi_cursor_demo.py が見つかりません"; \
	fi

# =============================================================================
# Broadcast Kitten Demo
# =============================================================================
broadcast:
	@echo "Broadcast Kitten デモを開始..."
	@if [ -f "$(DEMO_DIR)/broadcast_demo.sh" ]; then \
		$(DEMO_DIR)/broadcast_demo.sh all; \
	else \
		echo "broadcast_demo.sh が見つかりません"; \
	fi

broadcast-setup:
	@$(DEMO_DIR)/broadcast_demo.sh setup

broadcast-clean:
	@$(DEMO_DIR)/broadcast_demo.sh cleanup

# =============================================================================
# Cursor Trail Demo (v0.37+)
# =============================================================================
trail:
	@echo "Cursor Trail デモを開始..."
	@if [ -f "$(DEMO_DIR)/cursor_trail_demo.sh" ]; then \
		$(DEMO_DIR)/cursor_trail_demo.sh all; \
	else \
		echo "cursor_trail_demo.sh が見つかりません"; \
	fi

# =============================================================================
# Hints Kitten Demo
# =============================================================================
hints:
	@echo "Hints Kitten デモを開始..."
	@if [ -f "$(DEMO_DIR)/hints_demo.sh" ]; then \
		$(DEMO_DIR)/hints_demo.sh all; \
	else \
		echo "hints_demo.sh が見つかりません"; \
	fi

# =============================================================================
# SSH Kitten Demo
# =============================================================================
ssh:
	@echo "SSH Kitten デモを開始..."
	@if [ -f "$(DEMO_DIR)/ssh_demo.sh" ]; then \
		$(DEMO_DIR)/ssh_demo.sh all; \
	else \
		echo "ssh_demo.sh が見つかりません"; \
	fi

# =============================================================================
# All Demos
# =============================================================================
all: demo
	@echo ""
	@read -p "マルチサーバーデモも実行しますか？ [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) multi; \
	fi

# =============================================================================
# Status & Cleanup
# =============================================================================
status:
	@echo "=== Demo Status ==="
	@echo ""
	@echo "ログディレクトリ: $(LOG_DIR)"
	@ls -la $(LOG_DIR)/*.log 2>/dev/null || echo "  ログファイルなし"
	@echo ""
	@echo "起動中のプロセス:"
	@ps aux | grep -E "http.server 808[0-2]" | grep -v grep || echo "  なし"
	@echo ""
	@echo "kitty タブ:"
	@kitten @ ls 2>/dev/null | grep -E '"title":' | head -10 || echo "  取得できません"

clean:
	@echo "クリーンアップ中..."
	@# サーバープロセスを停止
	@for port in 8080 8081 8082; do \
		pkill -f "python3 -m http.server $$port" 2>/dev/null || true; \
	done
	@# PIDファイルを削除
	@rm -f $(LOG_DIR)/*.pid 2>/dev/null || true
	@# ログファイルを削除
	@rm -f $(LOG_DIR)/*.log 2>/dev/null || true
	@# デモ用タブを閉じる
	@kitten @ close-tab -m title:Control 2>/dev/null || true
	@kitten @ close-tab -m title:Observe 2>/dev/null || true
	@kitten @ close-tab -m title:Interact 2>/dev/null || true
	@kitten @ close-tab -m title:Analyze 2>/dev/null || true
	@echo "完了"

# =============================================================================
# Log Router
# =============================================================================
log-summary:
	@if [ -f "$(LOG_DIR)/combined.log" ]; then \
		python3 $(DEMO_DIR)/log_router.py $(LOG_DIR)/combined.log --summarize; \
	else \
		echo "ログファイルがありません。先に 'make multi' を実行してください。"; \
	fi

log-errors:
	@if [ -f "$(LOG_DIR)/combined.log" ]; then \
		python3 $(DEMO_DIR)/log_router.py $(LOG_DIR)/combined.log --level ERROR; \
	else \
		echo "ログファイルがありません。"; \
	fi

log-claude:
	@if [ -f "$(LOG_DIR)/combined.log" ]; then \
		python3 $(DEMO_DIR)/log_router.py $(LOG_DIR)/combined.log --claude-prompt; \
	else \
		echo "ログファイルがありません。"; \
	fi

# =============================================================================
# Quick Commands (LT用)
# =============================================================================
# LT中に使う最小コマンド
lt-rc:
	@echo "=== Remote Control Quick Demo ==="
	@kitten @ launch --type=tab --tab-title="Demo" --keep-focus
	@sleep 0.5
	@kitten @ set-tab-color -m title:Demo active_bg=#3b82f6
	@sleep 0.5
	@kitten @ send-text -m title:Demo "echo 'Hello from Remote Control!'\n"
	@sleep 1
	@kitten @ close-tab -m title:Demo

lt-tabs:
	@echo "=== 4タブ構成 Quick Setup ==="
	@$(DEMO_DIR)/orchestrate.sh setup
