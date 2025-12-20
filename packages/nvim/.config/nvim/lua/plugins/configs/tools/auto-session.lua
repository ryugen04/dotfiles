return {
  -- セッション
  {
    'rmagatti/auto-session',
    cond = not env.is_vscode(),
    config = function()
    
  require("auto-session").setup {
    log_level = "error",
    auto_session_suppress_dirs = { "~/dev/*" },
 }
    end,
    doc = "セッション管理"
  },
}
