-- Kotlin開発環境設定
-- kotlin.nvim (AlexandrosAlexiou/kotlin.nvim) + JetBrains kotlin-lsp v262
-- kotlin-lsp は Homebrew cask でインストール済み（/opt/homebrew/bin/kotlin-lsp）
-- キーバインドは whichkey.lua で管理
return {
	{
		"AlexandrosAlexiou/kotlin.nvim",
		ft = { "kotlin" },
		dependencies = {
			"williamboman/mason.nvim",
			"williamboman/mason-lspconfig.nvim",
			"folke/trouble.nvim",
		},
		config = function()
			-- Homebrew cask版kotlin-lspのパスを設定（Mason未使用時のフォールバック）
			if not vim.env.KOTLIN_LSP_DIR then
				local cask_dir = "/opt/homebrew/Caskroom/kotlin-lsp"
				local versions = vim.fn.glob(cask_dir .. "/*", false, true)
				if #versions > 0 then
					-- 最新バージョンのディレクトリを使用
					table.sort(versions)
					vim.env.KOTLIN_LSP_DIR = versions[#versions]
				end
			end

			require("kotlin").setup({
				root_markers = {
					"settings.gradle",
					"settings.gradle.kts",
					"build.gradle",
					"build.gradle.kts",
					"pom.xml",
					".git",
				},
				jvm_args = {
					"-Xmx4g",
				},
				inlay_hints = {
					enabled = true,
					parameters = true,
					parameters_compiled = true,
					parameters_excluded = false,
					types_property = true,
					types_variable = true,
					function_return = true,
					function_parameter = true,
					lambda_return = true,
					lambda_receivers_parameters = true,
					value_ranges = true,
					kotlin_time = true,
				},
			})
		end,
	},
	-- 旧プラグイン（無効化して残す。Detekt/テストランナーが必要になったら復活）
	-- {
	-- 	dir = "~/dev/projects/kotlin-extended-lsp.nvim",
	-- 	ft = "kotlin",
	-- 	config = function()
	-- 		require("kotlin-extended-lsp").setup({...})
	-- 	end,
	-- },
}
