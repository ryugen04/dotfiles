return {
  -- Git
  {
    'kdheepak/lazygit.nvim',
    cond = not env.is_vscode(),
    cmd = { "LazyGit", "LazyGitConfig", "LazyGitCurrentFile", "LazyGitFilter", "LazyGitFilterCurrentFile" },
    keys = {
      { "<leader>gg", "<cmd>LazyGit<cr>", desc = "LazyGit" },
    },
    dependencies = { 'nvim-telescope/telescope.nvim' },
    config = function()
      require('telescope').load_extension('lazygit')
      local group = vim.api.nvim_create_augroup("LazygitMods", { clear = true })
      vim.api.nvim_create_autocmd("TermEnter", {
        pattern = "*",
        group = group,
        callback = function()
          local name = vim.api.nvim_buf_get_name(0)
          if string.find(name, "lazygit") then
            vim.keymap.set("t", "<ESC>",
              function()
                -- Get the terminal job ID for the current buffer
                local bufnr = vim.api.nvim_get_current_buf()
                local chan = vim.b[bufnr].terminal_job_id
                if chan then
                  -- Send the ESC key sequence to the terminal
                  -- "\x1b" is the escape character
                  vim.api.nvim_chan_send(chan, "\x1b")
                end
                --vim.cmd([[call feedkeys("q")]])
              end,
              { buffer = true })
            return
          end
        end,
      })
    end,
    doc = "Git UI"
  },
  {
    'sindrets/diffview.nvim',
    cond = not env.is_vscode(),
    cmd = { "DiffviewOpen", "DiffviewClose", "DiffviewToggleFiles", "DiffviewFocusFiles", "DiffviewRefresh" },
  },
  {
    'APZelos/blamer.nvim',
    cond = not env.is_vscode(),
    event = "VeryLazy",  -- 遅延読み込み
    config = function()
      vim.g.blamer_enabled = 0  -- デフォルトでは無効（`:BlamerToggle`で有効化）
      vim.g.blamer_delay = 500
    end,
  },
  -- octo.nvim - GitHub PR/Issue操作
  {
    'pwntester/octo.nvim',
    cond = not env.is_vscode(),
    cmd = { "Octo" },
    dependencies = {
      'nvim-lua/plenary.nvim',
      'nvim-telescope/telescope.nvim',
      'nvim-tree/nvim-web-devicons',
    },
    config = function()
      require("octo").setup({
        use_local_fs = false,
        enable_builtin = true,
        default_remote = { "upstream", "origin" },
        ssh_aliases = {},
        picker = "telescope",
        picker_config = {
          use_emojis = true,
          mappings = {
            open_in_browser = { lhs = "<C-b>", desc = "ブラウザで開く" },
            copy_url = { lhs = "<C-y>", desc = "URLをコピー" },
            checkout_pr = { lhs = "<C-o>", desc = "PRをチェックアウト" },
            merge_pr = { lhs = "<C-r>", desc = "PRをマージ" },
          },
        },
        comment_icon = "▎",
        outdated_icon = "󰅒 ",
        resolved_icon = " ",
        reaction_viewer_hint_icon = " ",
        user_icon = " ",
        timeline_marker = " ",
        timeline_indent = "2",
        right_bubble_delimiter = "",
        left_bubble_delimiter = "",
        snippet_context_lines = 4,
        gh_env = {},
        timeout = 5000,
        default_to_projects_v2 = false,
        suppress_missing_scope = {
          projects_v2 = true,
        },
        ui = {
          use_signcolumn = true,
        },
        issues = {
          order_by = {
            field = "CREATED_AT",
            direction = "DESC",
          },
        },
        pull_requests = {
          order_by = {
            field = "CREATED_AT",
            direction = "DESC",
          },
          always_select_remote_on_create = false,
        },
        file_panel = {
          size = 10,
          use_icons = true,
        },
        mappings = {
          issue = {
            close_issue = { lhs = "<leader>oic", desc = "Issueを閉じる" },
            reopen_issue = { lhs = "<leader>oio", desc = "Issueを再開" },
            list_issues = { lhs = "<leader>oil", desc = "Issue一覧" },
            reload = { lhs = "<C-r>", desc = "リロード" },
            open_in_browser = { lhs = "<C-b>", desc = "ブラウザで開く" },
            copy_url = { lhs = "<C-y>", desc = "URLをコピー" },
            add_assignee = { lhs = "<leader>oaa", desc = "担当者を追加" },
            remove_assignee = { lhs = "<leader>oad", desc = "担当者を削除" },
            create_label = { lhs = "<leader>olc", desc = "ラベルを作成" },
            add_label = { lhs = "<leader>ola", desc = "ラベルを追加" },
            remove_label = { lhs = "<leader>old", desc = "ラベルを削除" },
            goto_issue = { lhs = "<leader>ogi", desc = "Issueへ移動" },
            add_comment = { lhs = "<leader>oca", desc = "コメントを追加" },
            delete_comment = { lhs = "<leader>ocd", desc = "コメントを削除" },
            next_comment = { lhs = "]c", desc = "次のコメント" },
            prev_comment = { lhs = "[c", desc = "前のコメント" },
            react_hooray = { lhs = "<leader>orp", desc = "🎉リアクション" },
            react_heart = { lhs = "<leader>orh", desc = "❤️リアクション" },
            react_eyes = { lhs = "<leader>ore", desc = "👀リアクション" },
            react_thumbs_up = { lhs = "<leader>or+", desc = "👍リアクション" },
            react_thumbs_down = { lhs = "<leader>or-", desc = "👎リアクション" },
            react_rocket = { lhs = "<leader>orr", desc = "🚀リアクション" },
            react_laugh = { lhs = "<leader>orl", desc = "😄リアクション" },
            react_confused = { lhs = "<leader>orc", desc = "😕リアクション" },
          },
          pull_request = {
            checkout_pr = { lhs = "<leader>opo", desc = "PRをチェックアウト" },
            merge_pr = { lhs = "<leader>opm", desc = "PRをマージ" },
            squash_and_merge_pr = { lhs = "<leader>ops", desc = "Squash & Merge" },
            list_commits = { lhs = "<leader>opc", desc = "コミット一覧" },
            list_changed_files = { lhs = "<leader>opf", desc = "変更ファイル一覧" },
            show_pr_diff = { lhs = "<leader>opd", desc = "PRのdiffを表示" },
            add_reviewer = { lhs = "<leader>ova", desc = "レビュアーを追加" },
            remove_reviewer = { lhs = "<leader>ovd", desc = "レビュアーを削除" },
            close_issue = { lhs = "<leader>oic", desc = "PRを閉じる" },
            reopen_issue = { lhs = "<leader>oio", desc = "PRを再開" },
            list_issues = { lhs = "<leader>oil", desc = "Issue一覧" },
            reload = { lhs = "<C-r>", desc = "リロード" },
            open_in_browser = { lhs = "<C-b>", desc = "ブラウザで開く" },
            copy_url = { lhs = "<C-y>", desc = "URLをコピー" },
            goto_file = { lhs = "gf", desc = "ファイルへ移動" },
            add_assignee = { lhs = "<leader>oaa", desc = "担当者を追加" },
            remove_assignee = { lhs = "<leader>oad", desc = "担当者を削除" },
            create_label = { lhs = "<leader>olc", desc = "ラベルを作成" },
            add_label = { lhs = "<leader>ola", desc = "ラベルを追加" },
            remove_label = { lhs = "<leader>old", desc = "ラベルを削除" },
            goto_issue = { lhs = "<leader>ogi", desc = "Issueへ移動" },
            add_comment = { lhs = "<leader>oca", desc = "コメントを追加" },
            delete_comment = { lhs = "<leader>ocd", desc = "コメントを削除" },
            next_comment = { lhs = "]c", desc = "次のコメント" },
            prev_comment = { lhs = "[c", desc = "前のコメント" },
            react_hooray = { lhs = "<leader>orp", desc = "🎉リアクション" },
            react_heart = { lhs = "<leader>orh", desc = "❤️リアクション" },
            react_eyes = { lhs = "<leader>ore", desc = "👀リアクション" },
            react_thumbs_up = { lhs = "<leader>or+", desc = "👍リアクション" },
            react_thumbs_down = { lhs = "<leader>or-", desc = "👎リアクション" },
            react_rocket = { lhs = "<leader>orr", desc = "🚀リアクション" },
            react_laugh = { lhs = "<leader>orl", desc = "😄リアクション" },
            react_confused = { lhs = "<leader>orc", desc = "😕リアクション" },
          },
          review_thread = {
            goto_issue = { lhs = "<leader>ogi", desc = "Issueへ移動" },
            add_comment = { lhs = "<leader>oca", desc = "コメントを追加" },
            add_suggestion = { lhs = "<leader>osa", desc = "提案を追加" },
            delete_comment = { lhs = "<leader>ocd", desc = "コメントを削除" },
            next_comment = { lhs = "]c", desc = "次のコメント" },
            prev_comment = { lhs = "[c", desc = "前のコメント" },
            select_next_entry = { lhs = "]q", desc = "次のエントリ" },
            select_prev_entry = { lhs = "[q", desc = "前のエントリ" },
            select_first_entry = { lhs = "[Q", desc = "最初のエントリ" },
            select_last_entry = { lhs = "]Q", desc = "最後のエントリ" },
            close_review_tab = { lhs = "<C-c>", desc = "レビュータブを閉じる" },
            react_hooray = { lhs = "<leader>orp", desc = "🎉リアクション" },
            react_heart = { lhs = "<leader>orh", desc = "❤️リアクション" },
            react_eyes = { lhs = "<leader>ore", desc = "👀リアクション" },
            react_thumbs_up = { lhs = "<leader>or+", desc = "👍リアクション" },
            react_thumbs_down = { lhs = "<leader>or-", desc = "👎リアクション" },
            react_rocket = { lhs = "<leader>orr", desc = "🚀リアクション" },
            react_laugh = { lhs = "<leader>orl", desc = "😄リアクション" },
            react_confused = { lhs = "<leader>orc", desc = "😕リアクション" },
          },
          submit_win = {
            approve_review = { lhs = "<C-a>", desc = "レビューを承認" },
            comment_review = { lhs = "<C-m>", desc = "コメントレビュー" },
            request_changes = { lhs = "<C-r>", desc = "変更をリクエスト" },
            close_review_tab = { lhs = "<C-c>", desc = "レビュータブを閉じる" },
          },
          review_diff = {
            add_review_comment = { lhs = "<leader>oca", desc = "レビューコメントを追加" },
            add_review_suggestion = { lhs = "<leader>osa", desc = "レビュー提案を追加" },
            focus_files = { lhs = "<leader>oe", desc = "ファイルパネルにフォーカス" },
            toggle_files = { lhs = "<leader>ob", desc = "ファイルパネルを切り替え" },
            next_thread = { lhs = "]t", desc = "次のスレッド" },
            prev_thread = { lhs = "[t", desc = "前のスレッド" },
            select_next_entry = { lhs = "]q", desc = "次のエントリ" },
            select_prev_entry = { lhs = "[q", desc = "前のエントリ" },
            select_first_entry = { lhs = "[Q", desc = "最初のエントリ" },
            select_last_entry = { lhs = "]Q", desc = "最後のエントリ" },
            close_review_tab = { lhs = "<C-c>", desc = "レビュータブを閉じる" },
            toggle_viewed = { lhs = "<leader>o<space>", desc = "表示済みを切り替え" },
            goto_file = { lhs = "gf", desc = "ファイルへ移動" },
          },
          file_panel = {
            next_entry = { lhs = "j", desc = "次のエントリ" },
            prev_entry = { lhs = "k", desc = "前のエントリ" },
            select_entry = { lhs = "<cr>", desc = "エントリを選択" },
            refresh_files = { lhs = "R", desc = "ファイル一覧をリフレッシュ" },
            focus_files = { lhs = "<leader>oe", desc = "ファイルパネルにフォーカス" },
            toggle_files = { lhs = "<leader>ob", desc = "ファイルパネルを切り替え" },
            select_next_entry = { lhs = "]q", desc = "次のエントリ" },
            select_prev_entry = { lhs = "[q", desc = "前のエントリ" },
            select_first_entry = { lhs = "[Q", desc = "最初のエントリ" },
            select_last_entry = { lhs = "]Q", desc = "最後のエントリ" },
            close_review_tab = { lhs = "<C-c>", desc = "レビュータブを閉じる" },
            toggle_viewed = { lhs = "<leader>o<space>", desc = "表示済みを切り替え" },
          },
        },
      })
    end,
  },
}
