local M = {}

function M.setup()
  -- プラグインドキュメント生成
  vim.api.nvim_create_user_command("GeneratePluginDocs", function()
    require("plugins.tools.doc_generator").generate_docs()
  end, {})

  -- メモ関連のコマンド
  vim.api.nvim_create_user_command('CmMemo', function(opts)
    vim.cmd.edit(vim.fn.expand("~/dev/memo/" .. os.date("%Y%m%d") .. "memo.md"))
  end, {})

  vim.api.nvim_create_user_command('CmTodo', function(opts)
    vim.cmd.edit(vim.fn.expand("~/dev/Todo.md"))
  end, {})

  vim.api.nvim_create_user_command('CmCdVimSetting', function(opts)
    vim.cmd.cd(vim.fn.expand("~/.vim"))
  end, {})

  vim.api.nvim_create_user_command('CmReplaceCrlfToLf', function(opts)
    vim.cmd([[%s/\r//ge]])
  end, {})

  vim.api.nvim_create_user_command('CmCamelCaseToSnakeCase', function(opts)
    vim.cmd([['<,'>s/\([a-z0-9]\)\([A-Z]\)/\1_\l\2/g]])
  end, {})

  vim.api.nvim_create_user_command('CmSnakeCaseToCamelCase', function(opts)
    vim.cmd([['<,'>s/_\([a-z]\)/\u\1/g]])
  end, {})

  vim.api.nvim_create_user_command('CloseBuffers', function()
    local current_buf = vim.api.nvim_get_current_buf()
    local buffers_to_keep = {}
    local closed_count = 0

    -- 現在のバッファと変更のあるバッファをリストに追加
    for _, buf in ipairs(vim.api.nvim_list_bufs()) do
      if vim.api.nvim_buf_get_option(buf, 'modified') or buf == current_buf then
        table.insert(buffers_to_keep, buf)
      end
    end

    -- 保持するバッファ以外を閉じる
    for _, buf in ipairs(vim.api.nvim_list_bufs()) do
      if not vim.tbl_contains(buffers_to_keep, buf) then
        if pcall(vim.api.nvim_buf_delete, buf, { force = false }) then
          closed_count = closed_count + 1
        end
      end
    end
    vim.notify(closed_count .. " buffers closed", vim.log.levels.INFO)
  end, {})
end

M.setup()

return M
