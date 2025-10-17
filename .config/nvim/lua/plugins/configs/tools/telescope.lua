return {
  -- ファイル操作
  {
    'nvim-telescope/telescope-fzf-native.nvim',
    cond = not is_vscode,
    build = 'make',
  },
  {
    'nvim-telescope/telescope.nvim',
    cond = not env.is_vscode(),
    dependencies = {
      'nvim-lua/plenary.nvim',

      'nvim-telescope/telescope-file-browser.nvim',
    },
    config = function()
      local telescope = require('telescope')
      local actions = require('telescope.actions')
      local fb_actions = telescope.extensions.file_browser.actions
      local state = require('telescope.actions.state')
      local fb_utils = require("telescope._extensions.file_browser.utils")
      local Path = require("plenary.path")

      -- 現在のファイルブラウザのディレクトリを取得する関数
      local function get_current_dir(prompt_bufnr)
        local current_picker = state.get_current_picker(prompt_bufnr)
        local finder = current_picker.finder
        return finder.path
      end

      local function get_file_name_first(_, path)
        local tail = vim.fs.basename(path)
        local parent = vim.fs.dirname(path)
        if parent == "." then return tail end
        return string.format("%s\t\t%s", tail, parent)
      end

      telescope.setup({
        defaults = {
          file_ignore_patterns = {
            -- 検索から除外するものを定
            "^.git/",
            "^.cache/",
          },
          pickers = {
            find_files = {
              hidden = true,
              follow = true,
              no_ignore = true,
            },
          },
          vimgrep_arguments = {
            -- ripggrepコマンドのオプション
            "rg",
            "--color=never",
            "--no-heading",
            "--with-filename",
            "--line-number",
            "--column",
            "--smart-case",
            "-uu",
            "--hidden", -- 隠しファイルも検索
            "--follow"  -- シンボリックリンクをたどる
          },
        },
        pickers = {
          find_files = {
            hidden = true,     -- 隠しファイルを表示
            no_ignore = false, -- .gitignoreを尊重
            follow = true,     -- シンボリックリンクを追跡
            path_display = get_file_name_first,     -- シンボリックリンクを追跡
          },
          live_grep = {
            hidden = true,     -- 隠しファイルを表示
            no_ignore = false, -- .gitignoreを尊重
            follow = true,     -- シンボリックリンクを追跡
            path_display = get_file_name_first,     -- シンボリックリンクを追跡
          },
          buffers = {
            hidden = true,     -- 隠しファイルを表示
            no_ignore = false, -- .gitignoreを尊重
            follow = true,     -- シンボリックリンクを追跡
            path_display = get_file_name_first,     -- シンボリックリンクを追跡
          },
        },
        extensions = {
          -- ソート性能を大幅に向上させるfzfを使う
          fzf = {
            fuzzy = true,
            override_generic_sorter = true,
            override_file_sorter = true,
            case_mode = "smart_case",
          },
          file_browser = {
            -- ファイルブラウザの設定
            hijack_netrw = true,
            hidden = { file_browser = true, folder_browser = true },
            mappings = {
              ["i"] = {
                -- 現在のディレクトリでファイル検索
                ["<c-f>"] = function(prompt_bufnr)
                  -- 現在のファイルブラウザのディレクトリを取得
                  local current_dir = get_current_dir(prompt_bufnr)

                  if vim.fn.isdirectory(current_dir) == 0 then
                    -- ファイルが選択されている場合は、そのファイルのディレクトリを使用
                    current_dir = vim.fn.fnamemodify(current_dir, ':h')
                  end
                  actions.close(prompt_bufnr)
                  require("telescope.builtin").find_files({
                    cwd = current_dir,
                    hidden = true
                  })
                end,
                -- 現在のディレクトリでgrep検索
                ["<c-g>"] = function(prompt_bufnr)
                  local current_dir = get_current_dir(prompt_bufnr)
                  if vim.fn.isdirectory(current_dir) == 0 then
                    -- ファイルが選択されている場合は、そのファイルのディレクトリを使用
                    current_dir = vim.fn.fnamemodify(current_dir, ':h')
                  end
                  actions.close(prompt_bufnr)
                  require("telescope.builtin").live_grep({
                    cwd = current_dir,
                    hidden = true
                  })
                end,
              },
            },
          },
        },
      })
      require("telescope").load_extension("file_browser")
      require("telescope").load_extension("fzf")
    end,
    doc = "ファジーファインダー"
  },
}
