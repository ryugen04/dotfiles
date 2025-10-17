return {

  {
    'nvim-tree/nvim-tree.lua',
    cond = not env.is_vscode(),
    dependencies = { 'nvim-tree/nvim-web-devicons' },
    cmd = { 'NvimTreeOpen', 'NvimTreeClose', 'NvimTreeFocus', 'NvimTreeToggle' },
    config = function()
      local api = require('nvim-tree.api')

      -- キーマッピングの設定
      local function on_attach(bufnr)
        local function map(key, action, desc)
          vim.keymap.set('n', key, action, {
            desc = 'nvim-tree: ' .. desc,
            buffer = bufnr,
            noremap = true,
            silent = true,
            nowait = true
          })
        end

        -- 基本操作
        map('<CR>', api.node.open.edit, 'Open')
        map('o', api.node.open.edit, 'Open')
        map('<C-v>', api.node.open.vertical, 'Open: Vertical Split')
        map('<C-s>', api.node.open.horizontal, 'Open: Horizontal Split')
        map('<BS>', api.node.navigate.parent_close, 'Up')
        map('<Tab>', api.node.open.preview, 'Open Preview')
        map('-', api.tree.change_root_to_node, 'CD')

        -- ナビゲーション
        map('>', api.node.navigate.sibling.next, 'Next Sibling')
        map('<', api.node.navigate.sibling.prev, 'Previous Sibling')
        map('P', api.node.navigate.parent, 'Parent Directory')
        map('J', api.node.navigate.sibling.last, 'Last Sibling')
        map('K', api.node.navigate.sibling.first, 'First Sibling')

        -- ファイル操作
        map('a', api.fs.create, 'Create')
        map('d', api.fs.remove, 'Delete')
        map('D', api.fs.trash, 'Trash')
        map('r', api.fs.rename, 'Rename')
        map('x', api.fs.cut, 'Cut')
        map('c', api.fs.copy.node, 'Copy')
        map('p', api.fs.paste, 'Paste')

        -- その他
        map('R', api.tree.reload, 'Refresh')
        map('?', api.tree.toggle_help, 'Help')
        map('q', api.tree.close, 'Close')

        -- copy

        map('gy', api.fs.copy.absolute_path, 'Copy Absolute Path')

        map('y', api.fs.copy.filename, 'Copy Name')
        map('Y', api.fs.copy.relative_path, 'Copy Relative Path')
        map('<2-LeftMouse>', api.node.open.edit, 'Open')
        map('<2-RightMouse>', api.tree.change_root_to_node, 'CD')
      end


      local function setup_diagnostics_refresh()
        -- オリジナルのハンドラを保存
        local original_handler = vim.diagnostic.handlers.virtual_text

        -- 診断情報が更新されたときのハンドラをカスタマイズ
        vim.diagnostic.handlers.virtual_text = {
          show = function(namespace, bufnr, diagnostics, opts)
            original_handler.show(namespace, bufnr, diagnostics, opts)
            -- バッファが有効な場合のみリフレッシュを実行
            if vim.api.nvim_buf_is_valid(bufnr) then
              vim.defer_fn(function()
                api.tree.reload()
              end, 100)
            end
          end,
          hide = function(namespace, bufnr)
            original_handler.hide(namespace, bufnr)
            if vim.api.nvim_buf_is_valid(bufnr) then
              vim.defer_fn(function()
                api.tree.reload()
              end, 100)
            end
          end,
        }

        -- LSPの診断情報変更時のイベントハンドラを設定
        vim.api.nvim_create_autocmd("DiagnosticChanged", {
          group = vim.api.nvim_create_augroup("NvimTreeDiagnostics", { clear = true }),
          callback = function()
            vim.defer_fn(function()
              -- ツリーが表示されている場合のみリフレッシュ
              if api.tree.is_visible() then
                api.tree.reload()
              end
            end, 100)
          end,
        })
      end

      -- nvim-treeの設定
      require('nvim-tree').setup({
        disable_netrw = true,
        hijack_netrw = true,
        hijack_cursor = false,
        auto_close = true,
        sync_root_with_cwd = true,
        update_cwd = false,
        open_on_tab = false,
        filesystem_watchers = {
          enable = true,            -- ファイルシステムの監視を有効化
          debounce_delay = 50,      -- 更新の遅延時間
          ignore_dirs = { ".git" }, -- 監視から除外するディレクトリ
        },

        -- 自動更新の設定
        auto_reload_on_write = true,
        reload_on_bufenter = true, -- バッファ切り替え時に更新
        update_focused_file = {
          enable = true,           -- フォーカスされたファイルの状態を更新
          update_root = false,     -- ルートディレクトリは更新しない
          ignore_list = {},        -- 更新を無視するパターン
        },
        view = {
          width = 40,
          side = 'left',
          preserve_window_proportions = true,
        },
        renderer = {
          add_trailing = false,
          highlight_git = true,
          highlight_opened_files = "none",
          indent_markers = {
            enable = true,
          },
          icons = {
            git_placement = "signcolumn",
            show = {
              file = true,
              folder = true,
              folder_arrow = true,
              git = true,
            },
            glyphs = {
              default = "",
              symlink = "",
              git = {
                unstaged = "M",
                staged = "✓",
                unmerged = "",
                renamed = "➜",
                untracked = "★",
                deleted = "",
                ignored = "◌",
              },
              folder = {
                default = "",
                open = "",
                symlink = "",
                empty = "",
                empty_open = "",
                symlink_open = "",
              },
            },
          },
        },
        actions = {
          open_file = {
            window_picker = {
              enable = true,
            },
          },
          change_dir = {
            enable = true,
            global = false,
          },
        },
        modified = {
          enable = true,
          show_on_dirs = true,
          show_on_open_dirs = true,
        },
        diagnostics = {
          enable = true,
          show_on_dirs = true,
          show_on_open_dirs = true, -- 開いているディレクトリでも表示
          debounce_delay = 50,      -- 更新の遅延時間
          severity = {
            min = vim.diagnostic.severity.HINT,
            max = vim.diagnostic.severity.ERROR,
          },
          icons = {
            hint = "󱄋",
            info = "",
            warning = "",
            error = "",
          },
        },
        filters = {
          dotfiles = false,
          custom = { "^.git$" },
        },
        git = {
          enable = true,
          ignore = false,
          timeout = 500,
        },
        on_attach = on_attach,
      })
      setup_diagnostics_refresh()
    end,
    doc = "ファイルエクスプローラー"
  },

}
