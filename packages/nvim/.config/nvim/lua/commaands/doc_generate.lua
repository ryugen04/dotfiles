local M = {}

-- プラグイン設定ディレクトリのパスを取得
local function get_plugin_config_path()
  return vim.fn.stdpath("config") .. "/lua/plugins/configs"
end

-- カテゴリ名をフォーマット
local function format_category(category)
  return category:gsub("^%l", string.upper)
end

-- プラグイン情報を収集
local function collect_plugins(category_path)
  local plugins = {}
  local init_path = category_path .. "/init.lua"

  if vim.fn.filereadable(init_path) == 1 then
    local content = loadfile(init_path)
    if content then
      local plugin_specs = content()
      if type(plugin_specs) == "table" then
        for _, spec in ipairs(plugin_specs) do
          if type(spec) == "table" and spec[1] then
            table.insert(plugins, {
              name = spec[1],
              purpose = spec.doc or "No description provided",
              config = category_path:gsub(get_plugin_config_path() .. "/", ""),
            })
          end
        end
      end
    end
  end

  return plugins
end

-- Markdownテーブルの行を生成
local function generate_table_row(plugin)
  return string.format("| %s | %s | %s |", plugin.name, plugin.purpose, plugin.config)
end

-- カテゴリの説明を取得
local category_descriptions = {
  coding = "LSP、補完、デバッグなどの開発機能",
  editor = "エディタとしての機能拡張",
  ui = "見た目と表示に関する機能",
  tools = "ユーティリティ機能",
  lang = "言語固有の設定とプラグイン",
}

-- ドキュメントを生成
function M.generate_docs()
  local docs = {
    "# Neovim Plugin Management\n",
    "## Plugin Categories\n"
  }

  local config_path = get_plugin_config_path()
  local categories = vim.fn.readdir(config_path)

  for _, category in ipairs(categories) do
    -- READMEやdoc_generator自体をスキップ
    if category ~= "README.md" and not category:match("^%.") then
      local formatted_category = format_category(category)
      local description = category_descriptions[category] or ""

      table.insert(docs, string.format("### %s", formatted_category))
      table.insert(docs, description .. "\n")
      table.insert(docs, "| Plugin | Purpose | Config Location |")
      table.insert(docs, "|---------|----------|-----------------|")

      local plugins = collect_plugins(config_path .. "/" .. category)
      for _, plugin in ipairs(plugins) do
        table.insert(docs, generate_table_row(plugin))
      end
      table.insert(docs, "\n")
    end
  end

  -- READMEファイルに書き出し
  local readme_path = config_path .. "/README.md"
  local file = io.open(readme_path, "w")
  if file then
    file:write(table.concat(docs, "\n"))
    file:close()
    print("Plugin documentation has been updated at: " .. readme_path)
  else
    error("Failed to write documentation to: " .. readme_path)
  end
end

return M
