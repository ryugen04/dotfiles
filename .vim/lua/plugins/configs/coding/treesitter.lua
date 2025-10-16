return {

  -- シンタックス
  {
    'nvim-treesitter/nvim-treesitter',
    cond = not env.is_vscode(),
    event = { "BufReadPost", "BufNewFile" },  -- ファイル読み込み時に遅延読み込み
    cmd = { "TSInstall", "TSBufEnable", "TSBufDisable", "TSModuleInfo" },
    build = ":TSUpdate",
    config = function()
      require('nvim-treesitter.configs').setup({
        ensure_installed = {
          'lua',
          'vim',
          'bash',
          'c',
          'cpp',
          'css',
          'go',
          'html',
          'java',
          'javascript',
          'json',
          'python',
          'rust',
          'typescript',
          'yaml',
          'ruby'
        },
        highlight = {
          enable = true,
          additional_vim_regex_highlighting = false,
          -- 大規模ファイルでハイライトを無効化
          disable = function(lang, buf)
            local max_filesize = 100 * 1024  -- 100KB
            local ok, stats = pcall(vim.loop.fs_stat, vim.api.nvim_buf_get_name(buf))
            if ok and stats and stats.size > max_filesize then
              return true
            end
          end,
        },
        indent = {
          enable = true,
        },
        incremental_selection = {
          enable = true,
          keymaps = {
            init_selection = "gnn",
            node_incremental = "grn",
            scope_incremental = "grc",
            node_decremental = "grm",
          },
        },
      })
    end,
    doc = "構文解析"
  },
  {
    'nvim-treesitter/nvim-treesitter-context',
    cond = not env.is_vscode(),
    event = { "BufReadPost", "BufNewFile" },  -- 遅延読み込み
    dependencies = { "nvim-treesitter/nvim-treesitter" },
  },
}
