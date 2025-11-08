-- kotlin-lspのサーバー機能をデバッグするスクリプト
-- 使用方法: Kotlinファイルを開いた状態で :luafile debug-kotlin-lsp.lua

local clients = vim.lsp.get_active_clients()

for _, client in ipairs(clients) do
  if client.name == 'kotlin_lsp' then
    print('=== kotlin-lsp Server Capabilities ===\n')

    local caps = client.server_capabilities

    -- 基本機能
    print('Basic Features:')
    print('  definitionProvider:', caps.definitionProvider and 'YES' or 'NO')
    print('  declarationProvider:', caps.declarationProvider and 'YES' or 'NO')
    print('  typeDefinitionProvider:', caps.typeDefinitionProvider and 'YES' or 'NO')
    print('  implementationProvider:', caps.implementationProvider and 'YES' or 'NO')
    print('  referencesProvider:', caps.referencesProvider and 'YES' or 'NO')
    print('')

    -- コード編集機能
    print('Code Editing:')
    print('  renameProvider:', caps.renameProvider and 'YES' or 'NO')
    print('  documentFormattingProvider:', caps.documentFormattingProvider and 'YES' or 'NO')
    print('  documentRangeFormattingProvider:', caps.documentRangeFormattingProvider and 'YES' or 'NO')
    print('  codeActionProvider:', caps.codeActionProvider and 'YES' or 'NO')
    print('')

    -- 情報提供機能
    print('Information:')
    print('  hoverProvider:', caps.hoverProvider and 'YES' or 'NO')
    print('  signatureHelpProvider:', caps.signatureHelpProvider and 'YES' or 'NO')
    print('  completionProvider:', caps.completionProvider and 'YES' or 'NO')
    print('  documentSymbolProvider:', caps.documentSymbolProvider and 'YES' or 'NO')
    print('  workspaceSymbolProvider:', caps.workspaceSymbolProvider and 'YES' or 'NO')
    print('')

    -- その他の機能
    print('Other Features:')
    print('  documentHighlightProvider:', caps.documentHighlightProvider and 'YES' or 'NO')
    print('  semanticTokensProvider:', caps.semanticTokensProvider and 'YES' or 'NO')
    print('  inlayHintProvider:', caps.inlayHintProvider and 'YES' or 'NO')
    print('')

    -- 詳細情報（JSON形式）
    print('\n=== Detailed Capabilities (JSON) ===')
    print(vim.inspect(caps))

    return
  end
end

print('kotlin-lsp client not found. Make sure a Kotlin file is open and the LSP is attached.')
print('\nActive clients:')
for _, client in ipairs(clients) do
  print('  - ' .. client.name)
end
