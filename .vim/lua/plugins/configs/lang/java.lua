local M = {}
-- カバレッジ関連のキーマップとコマンド追加
local function setup_jacoco_keymaps(bufnr)
  local function buf_map(mode, lhs, rhs, desc)
    vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, desc = desc })
  end


  -- カバレッジ結果をハイライト表示するコマンド
  vim.api.nvim_create_user_command('JaCoCoShow', function()
    require('jacoco').show()
  end, { desc = 'Show JaCoCo coverage' })

  -- カバレッジレポートを生成するコマンド
  vim.api.nvim_create_user_command('JaCoCoRun', function()
    require('jacoco').run()
  end, { desc = 'Run tests with JaCoCo' })
end

local function setup_keymaps(bufnr)
  local function buf_map(mode, lhs, rhs, desc)
    vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, desc = desc })
  end

  -- LSP関連のキーマップ
  buf_map('n', '<leader>Jo', function() require('jdtls').organize_imports() end, "[J]ava [O]rganize Imports")
  buf_map('n', '<leader>Jv', function() require('jdtls').extract_variable() end, "[J]ava Extract [V]ariable")
  buf_map('v', '<leader>Jv', function() require('jdtls').extract_variable(true) end, "[J]ava Extract [V]ariable")
  buf_map('n', '<leader>JC', function() require('jdtls').extract_constant() end, "[J]ava Extract [C]onstant")
  buf_map('v', '<leader>JC', function() require('jdtls').extract_constant(true) end, "[J]ava Extract [C]onstant")
  buf_map('n', '<leader>Jt', function() require('jdtls').test_nearest_method() end, "[J]ava [T]est Method")
  buf_map('n', '<leader>JT', function() require('jdtls').test_class() end, "[J]ava [T]est Class")

  -- Spring Boot関連のキーマップ
  buf_map('n', '<leader>Jj', function() require('jacoco').run() end, "[J]ava [J]aCoCoレポート生成")
  buf_map('n', '<leader>JJ', function() require('jacoco').show() end, "[J]ava [J]aCoCoレポート表示")
  buf_map('n', '<leader>JC', function() require('jacoco').clear() end, "[J]ava [C]lear JaCoCo display")
  buf_map('n', '<leader>Jo', function() require('jacoco').open_html_report() end, "[J]ava [O]pen HTML report")
  buf_map('n', '<leader>Jt', function() require('jacoco').toggle() end, "[J]ava [T]oggle JaCoCo on/off")
  buf_map('n', '<leader>Jm', function() require('jacoco').toggle_display_method() end, "[J]ava Toggle display [M]ethod")
  buf_map('n', '<leader>Js', function() require('jacoco').show_summary() end, "[J]ava [S]how coverage summary")
  buf_map('n', '<leader>Jp', function() require('jacoco').show_coverage_popup() end, "[J]ava Show coverage [P]opup")

  -- Spring Boot関連のデバッグキーマップを追加
  buf_map('n', '<leader>Jsd', function() vim.cmd('SpringBootDebug') end, "[J]ava [S]pring Boot [D]ebug")
  buf_map('n', '<leader>Jsr', function() vim.cmd('SpringBootRun') end, "[J]ava [S]pring Boot [R]un")
  buf_map('n', '<leader>Jss', function() vim.cmd('SpringBootDebugStart') end, "[J]ava [S]pring Boot Debug [S]tart")

  -- デバッグ操作キーマップ
  buf_map('n', '<leader>Jb', function() require('dap').toggle_breakpoint() end, "[J]ava Toggle [B]reakpoint")
  buf_map('n', '<leader>Jdb', function()
    vim.ui.input({ prompt = "Condition: " }, function(condition)
      if condition then
        require('dap').set_breakpoint(condition)
      end
    end)
  end, "[J]ava Set Con[d]itional [B]reakpoint")
  buf_map('n', '<leader>Jc', function() require('dap').continue() end, "[J]ava Debug [C]ontinue")
  buf_map('n', '<leader>Ji', function() require('dap').step_into() end, "[J]ava Step [I]nto")
  buf_map('n', '<leader>Jo', function() require('dap').step_over() end, "[J]ava Step [O]ver")
  buf_map('n', '<leader>Jou', function() require('dap').step_out() end, "[J]ava Step [O]ut")
  buf_map('n', '<leader>Jre', function() require('dap').repl.open() end, "[J]ava Open [Re]pl")
  buf_map('n', '<leader>Jq', function() require('dap').terminate() end, "[J]ava De[b]ug [Q]uit")

  -- UI関連
  buf_map('n', '<leader>Jdu', function() require('dapui').toggle() end, "[J]ava [D]AP [U]I toggle")
end

local function get_jdtls_config()
  local mason_registry = require("mason-registry")
  local jdtls_pkg = mason_registry.get_package("jdtls")
  local jdtls_path = jdtls_pkg:get_install_path()
  local lombok_path = jdtls_path .. "/lombok.jar"

  -- Lombokが存在しない場合、ダウンロード
  if vim.fn.filereadable(lombok_path) == 0 then
    vim.fn.system(string.format(
      "curl -L %s -o %s",
      "https://projectlombok.org/downloads/lombok.jar",
      lombok_path
    ))
  end

  -- Java Debug Adapterの設定
  local bundles = {}
  local java_debug_pkg = mason_registry.get_package("java-debug-adapter")
  local java_test_pkg = mason_registry.get_package("java-test")

  vim.list_extend(bundles, vim.split(
    vim.fn.glob(java_debug_pkg:get_install_path() .. "/extension/server/com.microsoft.java.debug.plugin-*.jar"),
    "\n"
  ))
  vim.list_extend(bundles, vim.split(
    vim.fn.glob(java_test_pkg:get_install_path() .. "/extension/server/*.jar"),
    "\n"
  ))

  local root_dir = require('jdtls.setup').find_root({ '.git', 'mvnw', 'gradlew', 'pom.xml', 'build.gradle' })
  -- デバッグ出力
  if root_dir then
    vim.notify("JDTLS root directory: " .. root_dir, vim.log.levels.INFO)
  else
    vim.notify("No root directory found! Markers searched: " .. vim.inspect(root_markers), vim.log.levels.WARN)
    -- フォールバックとして現在のディレクトリを使用
    root_dir = vim.fn.getcwd()
  end

  local workspace_dir = vim.fn.expand('~/.cache/jdtls-workspace/') .. vim.fn.fnamemodify(root_dir, ':p:h:t')


  return {
    cmd = {
      "java",
      "-Declipse.application=org.eclipse.jdt.ls.core.id1",
      "-Dosgi.bundles.defaultStartLevel=4",
      "-Declipse.product=org.eclipse.jdt.ls.core.product",
      "-Dlog.protocol=true",
      "-Dlog.level=ALL",
      "-Xms1g",
      "-Xmx2g",
      "--add-modules=ALL-SYSTEM",
      "--add-opens", "java.base/java.util=ALL-UNNAMED",
      "--add-opens", "java.base/java.lang=ALL-UNNAMED",
      "-javaagent:" .. lombok_path,
      "-jar", vim.fn.glob(jdtls_path .. "/plugins/org.eclipse.equinox.launcher_*.jar"),
      "-configuration", jdtls_path .. "/config_linux",
      "-data", workspace_dir
    },
    root_dir = root_dir,
    settings = {
      java = {
        configuration = {
          updateBuildConfiguration = "interactive",
          runtimes = {
            {
              name = "JavaSE-21",
              path = vim.fn.expand("$JAVA_HOME"),
            }
          }
        },
        eclipse = {
          downloadSources = true,
        },
        maven = {
          downloadSources = true,
          updateSnapshots = true,
        },
        implementationsCodeLens = {
          enabled = true,
        },
        referencesCodeLens = {
          enabled = true,
        },
        inlayHints = {
          parameterNames = {
            enabled = "all",
          },
        },
        signatureHelp = { enabled = true },
        completion = {
          favoriteStaticMembers = {
            "org.junit.jupiter.api.Assertions.*",
            "org.mockito.Mockito.*",
            "org.assertj.core.api.Assertions.*",
            "java.util.Objects.requireNonNull",
            "java.util.Objects.requireNonNullElse",
          },
          filteredTypes = {
            "com.sun.*",
            "io.micrometer.shaded.*",
            "java.awt.*",
            "jdk.*",
            "sun.*",
          },
        },
        sources = {
          organizeImports = {
            starThreshold = 9999,
            staticStarThreshold = 9999,
          },
        },
        codeGeneration = {
          toString = {
            template = "${object.className}{${member.name()}=${member.value}, ${otherMembers}}"
          },
          useBlocks = true,

        },
        debug = {
          settings = {
            hotCodeReplace = "auto",
            enableRunDebugCodeLens = true,
            -- 単一メソッドのデバッグを強制
            forceBuildBeforeLaunch = true,
            useInstanceScope = true,
            showQualifiedNames = true,
            showStaticVariables = true,
            -- テスト実行時の設定
            enableTestFilter = true,
            filterStackTraces = true,
            springBoot = {
              enableLiveBeanSupport = true,
              enableAutomaticRestart = true,
              enableJmxRetrying = true,
            }
          }
        },
        codeAction = {
          enableMavenSourceAction = true,
          enableGradleSourceAction = true,
        },
      },
    },

    init_options = {
      bundles = bundles,
      extendedClientCapabilities = {
        resolveAdditionalTextEditsSupport = true,
        -- デバッグ機能の詳細設定
        classFileContentsSupport = true,
        generateToStringPromptSupport = true,
        hashCodeEqualsPromptSupport = true,
        advancedExtractRefactoringSupport = true,
        advancedOrganizeImportsSupport = true,
        executeClientCommandSupport = true,
        progressReportSupport = true,
        -- テストに関する拡張設定
        testSupport = true,
        shouldLanguageServerExitOnShutdown = true,
      }
    },
    -- init_options = {
    --   bundles = bundles,
    --   extendedClientCapabilities = require('jdtls').extendedClientCapabilities,
    -- },
  }
end

return {
  {
    'mfussenegger/nvim-jdtls',
    cond = not env.is_vscode(),
    dependencies = {
      'mfussenegger/nvim-dap',
      'williamboman/mason.nvim',
    },
    ft = "java",
    config = function()
      -- JDTLSのセットアップ
      vim.api.nvim_create_autocmd("FileType", {
        pattern = "java",
        callback = function()
          local config = get_jdtls_config()
          config.on_attach = function(client, bufnr)
            setup_keymaps(bufnr)
            require('jdtls').setup_dap({ hotcodereplace = 'auto' })
            require('jdtls.dap').setup_dap_main_class_configs()
            require('jdtls.setup').add_commands()

            vim.api.nvim_buf_create_user_command(bufnr, 'JaCoCoShow', function()
              require('jacoco').show()
            end, { desc = 'Show JaCoCo coverage' })

            vim.api.nvim_buf_create_user_command(bufnr, 'JaCoCoRun', function()
              require('jacoco').run()
            end, { desc = 'Run tests with JaCoCo' })

            -- Spring Boot関連のコマンドを登録
            vim.api.nvim_buf_create_user_command(bufnr, 'SpringBootRun', function()
              local is_maven = vim.fn.filereadable(vim.fn.getcwd() .. '/pom.xml') == 1
              local cmd = is_maven
                  and 'mvn spring-boot:run -Dspring.profiles.active=local'
                  or './gradlew bootRun --args="--spring.profiles.active=local"'

              vim.cmd('tabnew | terminal ' .. cmd)
              vim.cmd('startinsert')
            end, { desc = 'Run Spring Boot Application' })

            vim.api.nvim_buf_create_user_command(bufnr, 'SpringBootDebug', function()
              local is_maven = vim.fn.filereadable(vim.fn.getcwd() .. '/pom.xml') == 1
              local debug_args =
              '-Dspring-boot.run.jvmArguments="-Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=y,address=5005"'
              local cmd = is_maven
                  and 'mvn spring-boot:run ' .. debug_args
                  or './gradlew bootRun --debug-jvm'

              vim.cmd('tabnew | terminal ' .. cmd)
              vim.cmd('startinsert')

              vim.defer_fn(function()
                require('dap').run({
                  type = 'java',
                  request = 'attach',
                  name = 'Attach to Spring Boot',
                  hostName = 'localhost',
                  port = 5005,
                })
              end, 2000)
            end, { desc = 'Debug Spring Boot Application' })
          end
          require('jdtls').start_or_attach(config)
        end
      })
    end,
  },
  {
    "nvimtools/none-ls.nvim",
    ft = "java",  -- Java専用に限定
    dependencies = {
      "nvimtools/none-ls-extras.nvim"
    },
    config = function()
      local nls = require("null-ls")
      local fmt = nls.builtins.formatting
      local dgn = nls.builtins.diagnostics
      local augroup = vim.api.nvim_create_augroup("LspFormatting", {})

      local mason_registry = require("mason-registry")
      local jdtls_pkg = mason_registry.get_package("jdtls")
      local jdtls_path = jdtls_pkg:get_install_path()
      local checkstyle_path = jdtls_path .. "/google-checks.xml"

      nls.setup({
        sources = {
          fmt.google_java_format.with({
            extra_args = {
              -- "--aosp" --indent4
            },
          }),

        },

        on_attach = function(client, bufnr)
          if client.supports_method("textDocument/formatting") then
            vim.api.nvim_clear_autocmds({ group = augroup, buffer = bufnr })
            vim.api.nvim_create_autocmd("BufWritePre", {
              group = augroup,
              buffer = bufnr,
              callback = function()
                vim.lsp.buf.format({ bufnr = bufnr })
              end
            })
          end
        end
      })
    end

  },
  {
    "mfussenegger/nvim-lint",
    ft = "java",  -- Java専用に限定
    config = function()
      -- require('lint').linters_by_ft = {
      --   java = { 'checkstyle' },
      -- }
      vim.api.nvim_create_autocmd({
        "BufWritePost"
      }, {
        callback = function()
          require("lint").try_lint()
          require("lint").try_lint("cspell")
        end
      })
    end
  },
  {
    "mfussenegger/nvim-dap",
    ft = "java",  -- Java専用に限定
    config = function()
      -- Simple configuration to attach to remote java debug process
      --
      require("jacoco").setup({
        -- JaCoCoの設定
        report_paths = {
          -- レポートパスの指定（プロジェクトによって異なる場合があります）
          -- Mavenプロジェクトの場合
          "target/site/jacoco/jacoco.xml",
          -- Gradleプロジェクトの場合
          "build/reports/jacoco/test/jacocoTestReport.xml",
        },
        display_method = "inline", -- 行番号の色を変更する方法
        -- カバレッジデータを表示するための設定
        signs = {
          covered = { text = "✓", texthl = "JacocoCovered" },
          missed = { text = "✘", texthl = "JacocoMissed" },
          partial = { text = "◑", texthl = "JacocoPartial" },
        },

        -- カスタムコマンド
        -- Mavenプロジェクトの場合のコマンド
        maven_command = "mvn test jacoco:report",
        -- Gradleプロジェクトの場合のコマンド
        gradle_command = "./gradlew test jacocoTestReport",

        -- プロジェクトタイプの自動検出（pom.xmlかbuild.gradleのどちらがあるか）
        auto_detect_project_type = true,
      })

      vim.api.nvim_set_hl(0, "JacocoCovered", { fg = "#00FF00" }) -- カバー済み: 緑色
      vim.api.nvim_set_hl(0, "JacocoMissed", { fg = "#FF0000" })  -- 未カバー: 赤色
      vim.api.nvim_set_hl(0, "JacocoPartial", { fg = "#FFFF00" }) -- 部分カバー: 黄色

      -- カバレッジハイライトの色設定
      vim.api.nvim_set_hl(0, "JacocoCoveredLine", { fg = "#00FF00", bold = true })
      vim.api.nvim_set_hl(0, "JacocoMissedLine", { fg = "#FF0000", bold = true })
      vim.api.nvim_set_hl(0, "JacocoPartialLine", { fg = "#FFFF00", bold = true })
    end,
  }
}
