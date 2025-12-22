-- Kotlin開発環境設定
-- kotlin-extended-lsp.nvim に機能を集約
-- キーバインドは whichkey.lua で管理
return {
	{
		dir = "~/dev/projects/kotlin-extended-lsp.nvim",
		ft = "kotlin",
		config = function()
			require("kotlin-extended-lsp").setup({
				debug_init_options = true,
				-- VSCode相当: --system-path オプション（キャッシュ・インデックス保存先）
				system_path = vim.fn.expand("~/Library/Caches/kotlin-lsp"),
				-- initializationOptions.cacheDirectory
				cache_directory = vim.fn.expand("~/Library/Caches/kotlin-lsp"),
				env = {
					GITHUB_TOKEN = os.getenv("GITHUB_TOKEN"),
					GITHUB_USER = os.getenv("GITHUB_USER"),
				},
			})
		end,
	},
}
