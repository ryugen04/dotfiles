local M = {}

-- 設定のデフォルト値
M.config = {
  report_paths = {
    "target/site/jacoco/",             -- Mavenの場合
    "build/reports/jacoco/test/html/", -- Gradleの場合
  },
  signs = {
    covered = { text = "✓", texthl = "JacocoCovered" },
    missed = { text = "✗", texthl = "JacocoMissed" },
    partial = { text = "◑", texthl = "JacocoPartial" },
  },
  display_method = "signs", -- "signs", "virtual_text", "highlight", "inline", "all"
  maven_command = "mvn test jacoco:report",
  gradle_command = "./gradlew test jacocoTestReport",
  auto_detect_project_type = true,
  debug_mode = true, -- デバッグモード（詳細なログを表示）
}

-- デバッグ出力関数
local function debug_log(message, level)
  if M.config.debug_mode then
    -- vim.notify("[JaCoCo] " .. message, level or vim.log.levels.INFO)
  end
end

-- 設定を初期化する関数
function M.setup(opts)
  M.config = vim.tbl_deep_extend("force", M.config, opts or {})

  -- サインの定義
  vim.fn.sign_define("jacoco_covered", M.config.signs.covered)
  vim.fn.sign_define("jacoco_missed", M.config.signs.missed)
  vim.fn.sign_define("jacoco_partial", M.config.signs.partial)

  -- 色の設定
  vim.api.nvim_set_hl(0, "JacocoCovered", { fg = "#00FF00" }) -- 緑色
  vim.api.nvim_set_hl(0, "JacocoMissed", { fg = "#FF0000" })  -- 赤色
  vim.api.nvim_set_hl(0, "JacocoPartial", { fg = "#FFFF00" }) -- 黄色

  -- 行番号ハイライト用の設定
  vim.api.nvim_set_hl(0, "JacocoCoveredLine", { fg = "#00FF00", bold = true }) -- 緑色の行番号
  vim.api.nvim_set_hl(0, "JacocoMissedLine", { fg = "#FF0000", bold = true })  -- 赤色の行番号
  vim.api.nvim_set_hl(0, "JacocoPartialLine", { fg = "#FFFF00", bold = true }) -- 黄色の行番号

  debug_log("JaCoCo setup complete")
end

-- プロジェクトタイプを検出する関数
local function detect_project_type()
  if vim.fn.filereadable("pom.xml") == 1 then
    return "maven"
  elseif vim.fn.filereadable("build.gradle") == 1 or vim.fn.filereadable("build.gradle.kts") == 1 then
    return "gradle"
  end

  return nil
end

-- JaCoCoレポートディレクトリを検索する関数
local function find_jacoco_report_dir()
  for _, report_path in ipairs(M.config.report_paths) do
    if vim.fn.isdirectory(report_path) == 1 then
      debug_log("JaCoCo report directory found at: " .. report_path)
      return report_path
    end
  end

  -- 現在のディレクトリからJaCoCoレポートディレクトリを検索
  local cmd = "find . -type d -path '*/jacoco*' | grep -v '/jacoco-agent/'"
  local handle = io.popen(cmd)
  if handle then
    local result = handle:read("*a")
    handle:close()

    local dirs = {}
    for path in result:gmatch("[^\r\n]+") do
      table.insert(dirs, path)
    end

    if #dirs > 0 then
      debug_log("Found JaCoCo report directories: " .. vim.inspect(dirs))
      return dirs[1] -- 最初に見つかったディレクトリを使用
    end
  end

  return nil
end

-- パッケージパスを作成する関数
local function get_package_path(java_file)
  local package_line = nil
  local file = io.open(java_file, "r")
  if file then
    -- ファイルの先頭からpackage文を検索
    for line in file:lines() do
      local package_match = line:match("package%s+([^;]+)")
      if package_match then
        package_line = package_match:gsub("%.", "/")
        break
      end
    end
    file:close()
  end

  return package_line
end

local function find_jacoco_html_report(current_filename)
  local report_dir = find_jacoco_report_dir()
  if not report_dir then
    vim.notify("No JaCoCo report directory found.", vim.log.levels.WARN)
    return nil
  end

  -- 現在のファイルのフルパスとパッケージを取得
  local current_file = vim.fn.expand("%:p")
  local package_path = get_package_path(current_file)

  debug_log("Searching for JaCoCo report with package: " .. (package_path or "unknown"))

  -- パッケージパスが取得できた場合、標準的なパスを構築して検索
  if package_path then
    -- パッケージパスのドットをスラッシュに変換
    local package_dir = package_path:gsub("%.", "/")

    -- ファイル名から.javaを除去
    local base_filename = current_filename:gsub("%.java$", "")

    -- 標準的なJaCoCoレポートパス
    local html_path = report_dir .. "/" .. package_dir .. "/" .. current_filename .. ".html"
    debug_log("Checking standard path: " .. html_path)

    if vim.fn.filereadable(html_path) == 1 then
      debug_log("Found JaCoCo HTML report at standard path: " .. html_path)
      return html_path
    end

    -- 変形バージョンも確認
    local alt_path = report_dir .. "/" .. package_dir .. "/" .. base_filename .. ".html"
    debug_log("Checking alternative path: " .. alt_path)

    if vim.fn.filereadable(alt_path) == 1 then
      debug_log("Found JaCoCo HTML report at alternative path: " .. alt_path)
      return alt_path
    end
  end

  -- 標準パスでの検索が失敗した場合、プロジェクト全体を検索
  debug_log("Standard path search failed, performing recursive search...")

  -- 複数の可能性を試す
  local search_patterns = {
    current_filename .. ".html",                    -- Calculator.java.html
    current_filename:gsub("%.java$", "") .. ".html" -- Calculator.html
  }

  for _, pattern in ipairs(search_patterns) do
    local cmd = "find " .. report_dir .. " -name '" .. pattern .. "'"
    debug_log("Running search command: " .. cmd)

    local handle = io.popen(cmd)
    if handle then
      local result = handle:read("*a")
      handle:close()

      local files = {}
      for path in result:gmatch("[^\r\n]+") do
        table.insert(files, path)
      end

      if #files > 0 then
        debug_log("Found JaCoCo HTML reports: " .. vim.inspect(files))
        return files[1] -- 最初に見つかったレポートを使用
      end
    end
  end

  vim.notify("No JaCoCo HTML report found for " .. current_filename, vim.log.levels.WARN)
  return nil
end
-- JaCoCoでテストを実行する関数
function M.run()
  local project_type = M.config.auto_detect_project_type and detect_project_type() or nil

  local cmd
  if project_type == "maven" then
    cmd = M.config.maven_command
  elseif project_type == "gradle" then
    cmd = M.config.gradle_command
  else
    vim.notify("Unknown project type. Cannot run JaCoCo.", vim.log.levels.ERROR)
    return
  end

  vim.notify("Running tests with JaCoCo...", vim.log.levels.INFO)

  -- コマンドを非同期で実行
  vim.fn.jobstart(cmd, {
    on_exit = function(_, code)
      if code == 0 then
        vim.notify("JaCoCo report generated successfully!", vim.log.levels.INFO)
        -- レポート生成後、自動的にカバレッジを表示
        M.show()
      else
        vim.notify("Failed to generate JaCoCo report. Exit code: " .. code, vim.log.levels.ERROR)
      end
    end,
    stdout_buffered = true,
    stderr_buffered = true,
  })
end

-- HTMLレポートからカバレッジデータを抽出する関数
local function parse_jacoco_html_report(html_path)
  if not html_path or vim.fn.filereadable(html_path) ~= 1 then
    vim.notify("JaCoCo HTML report not found at: " .. (html_path or "nil"), vim.log.levels.ERROR)
    return nil
  end

  -- HTMLファイルを読み込む
  local html_content = vim.fn.readfile(html_path)
  if not html_content or #html_content == 0 then
    vim.notify("JaCoCo HTML report is empty.", vim.log.levels.ERROR)
    return nil
  end

  debug_log("Parsing JaCoCo HTML report: " .. html_path)

  -- カバレッジデータ
  local coverage_data = {}

  -- HTMLを解析して行カバレッジを抽出
  local in_pre_section = false
  local line_number = nil

  for _, line in ipairs(html_content) do
    -- <pre class="source lang-java linenums"> セクションを検出
    if line:match('<pre class="source lang%-java linenums">') then
      in_pre_section = true
    elseif line:match('</pre>') then
      in_pre_section = false
    end

    -- <pre>セクション内のカバレッジ情報を抽出
    if in_pre_section then
      -- 行番号と条件のクラスを抽出
      local covered_match = line:match('<span class="([^"]+)" id="L(%d+)"')
      if covered_match then
        local class_name, line_nr = covered_match:match("([^%s]+)%s+id=\"L(%d+)\"")
        if not class_name or not line_nr then
          class_name, line_nr = covered_match, line:match('id="L(%d+)"')
        end

        if class_name and line_nr then
          line_number = tonumber(line_nr)

          local status
          if class_name == "fc" then
            status = "covered" -- 全カバー
          elseif class_name == "nc" then
            status = "missed"  -- 未カバー
          elseif class_name:match("^pc") then
            status = "partial" -- 部分カバー
          end

          if status and line_number then
            coverage_data[line_number] = { status = status }
            debug_log("Line " .. line_number .. " status: " .. status)
          end
        end
      end

      -- 条件分岐のカバレッジを抽出
      local branch_match = line:match('<span class="([^"]+)" title="([^"]+)"')
      if branch_match and line_number then
        local class_name, title = branch_match:match("([^%s]+)%s+title=\"([^\"]+)\"")
        if class_name and title then
          if class_name == "branchFC" or class_name == "branchPC" or class_name == "branchNC" then
            -- すでに行データがある場合のみ更新
            if coverage_data[line_number] then
              local status
              if class_name == "branchFC" then
                status = "covered"
              elseif class_name == "branchNC" then
                status = "missed"
              else
                status = "partial"
              end

              coverage_data[line_number].branch = {
                status = status,
                title = title
              }

              -- 部分カバーの場合
              if class_name == "branchPC" then
                coverage_data[line_number].status = "partial"
              end

              debug_log("Branch at line " .. line_number .. " status: " .. status .. " - " .. title)
            end
          end
        end
      end
    end
  end

  -- カバレッジデータの要約
  local covered_count = 0
  local missed_count = 0
  local partial_count = 0

  for _, data in pairs(coverage_data) do
    if data.status == "covered" then
      covered_count = covered_count + 1
    elseif data.status == "missed" then
      missed_count = missed_count + 1
    elseif data.status == "partial" then
      partial_count = partial_count + 1
    end
  end

  debug_log(string.format("Coverage summary: covered=%d, missed=%d, partial=%d",
    covered_count, missed_count, partial_count))

  return coverage_data
end

-- カバレッジ情報を可視化する関数
local function visualize_coverage(bufnr, coverage_data)
  if not coverage_data or vim.tbl_isempty(coverage_data) then
    vim.notify("No coverage data available for visualization", vim.log.levels.WARN)
    return 0
  end

  -- ネームスペースを作成
  local ns_id = vim.api.nvim_create_namespace("jacoco_coverage")

  -- 既存のハイライトをクリア
  vim.api.nvim_buf_clear_namespace(bufnr, ns_id, 0, -1)

  -- 行数をカウント
  local marked_lines = 0

  -- 各行にマーカーを設定
  for line_nr, data in pairs(coverage_data) do
    -- 行番号が有効かチェック
    if line_nr > 0 and line_nr <= vim.api.nvim_buf_line_count(bufnr) then
      local display_method = M.config.display_method
      local status = data.status

      -- サインを使用
      if display_method == "signs" or display_method == "all" then
        vim.fn.sign_place(
          line_nr,  -- 一意のID
          "jacoco", -- グループ名
          "jacoco_" .. status,
          bufnr,
          { lnum = line_nr }
        )
      end

      -- 行番号を装飾
      if display_method == "inline" or display_method == "all" then
        vim.api.nvim_buf_set_extmark(bufnr, ns_id, line_nr - 1, 0, {
          number_hl_group = "Jacoco" .. status:gsub("^%l", string.upper) .. "Line",
        })
      end

      -- 行全体にハイライトを適用
      if display_method == "highlight" or display_method == "all" then
        vim.api.nvim_buf_set_extmark(bufnr, ns_id, line_nr - 1, 0, {
          line_hl_group = "Jacoco" .. status:gsub("^%l", string.upper) .. "Bg",
          priority = 10, -- 低い優先度
        })
      end

      marked_lines = marked_lines + 1
    end
  end

  return marked_lines
end

-- カバレッジ情報を表示する関数
function M.show()
  local bufnr = vim.api.nvim_get_current_buf()
  local current_filename = vim.fn.expand("%:t")
  debug_log("Processing file: " .. current_filename)

  -- HTMLレポートファイルを検索
  local html_report_path = find_jacoco_html_report(current_filename)
  if not html_report_path then
    vim.notify("No JaCoCo HTML report found for " .. current_filename, vim.log.levels.WARN)
    return
  end

  -- HTMLレポートを解析
  local coverage_data = parse_jacoco_html_report(html_report_path)
  if not coverage_data or vim.tbl_isempty(coverage_data) then
    vim.notify("Failed to parse JaCoCo HTML report.", vim.log.levels.ERROR)
    return
  end

  -- カバレッジを可視化
  local marked_lines = visualize_coverage(bufnr, coverage_data)

  -- カバレッジの統計を計算
  local total_lines = vim.api.nvim_buf_line_count(bufnr)
  local covered_lines = 0
  local missed_lines = 0
  local partial_lines = 0

  for _, data in pairs(coverage_data) do
    if data.status == "covered" then
      covered_lines = covered_lines + 1
    elseif data.status == "missed" then
      missed_lines = missed_lines + 1
    elseif data.status == "partial" then
      partial_lines = partial_lines + 1
    end
  end

  if marked_lines > 0 then
    local coverage_percent = math.floor((covered_lines / marked_lines) * 100)
    vim.notify(
      string.format(
        "Coverage for %s: %d%% (%d covered, %d missed, %d partial out of %d instrumented lines)",
        current_filename, coverage_percent, covered_lines, missed_lines, partial_lines, marked_lines
      ),
      vim.log.levels.INFO
    )
  else
    vim.notify(
      "No lines were marked with coverage. Check your configuration.",
      vim.log.levels.WARN
    )
  end
end

-- HTMLレポートを外部ブラウザで開く関数
function M.open_html_report()
  local current_filename = vim.fn.expand("%:t")
  local html_report_path = find_jacoco_html_report(current_filename)

  if not html_report_path then
    vim.notify("No JaCoCo HTML report found for " .. current_filename, vim.log.levels.WARN)
    return
  end

  -- ブラウザで開く
  local cmd
  if vim.fn.has("mac") == 1 then
    cmd = "open " .. html_report_path
  elseif vim.fn.has("unix") == 1 then
    cmd = "xdg-open " .. html_report_path
  elseif vim.fn.has("win32") == 1 then
    cmd = "start " .. html_report_path
  else
    vim.notify("Unsupported platform for opening HTML report", vim.log.levels.ERROR)
    return
  end

  vim.fn.jobstart(cmd, {
    on_exit = function(_, code)
      if code ~= 0 then
        vim.notify("Failed to open HTML report: " .. html_report_path, vim.log.levels.ERROR)
      end
    end
  })

  vim.notify("Opening JaCoCo HTML report in browser: " .. html_report_path, vim.log.levels.INFO)
end

-- テストをJaCoCoで実行するための便利関数
function M.run_with_jacoco()
  -- 既存のJDTLSテスト実行関数を呼び出し
  local java_test = require('jdtls').test_class

  java_test()

  -- テストが終わった後にJaCoCoレポートを生成
  M.run()
end

-- デバッグ情報を出力する関数
function M.debug_info()
  local current_filename = vim.fn.expand("%:t")
  local info = {
    config = M.config,
    current_file = vim.fn.expand("%:p"),
    current_filename = current_filename,
    package = get_package_path(vim.fn.expand("%:p")),
    cwd = vim.fn.getcwd(),
    report_dir = find_jacoco_report_dir(),
    html_report = find_jacoco_html_report(current_filename)
  }

  vim.notify("JaCoCo Debug Info:\n" .. vim.inspect(info), vim.log.levels.INFO)

  -- HTMLレポートが存在する場合、その内容をプレビュー
  if info.html_report and vim.fn.filereadable(info.html_report) == 1 then
    local content = vim.fn.readfile(info.html_report, "", 30)
    vim.notify("HTML Report Preview:\n" .. table.concat(content, "\n"), vim.log.levels.INFO)
  end
end

-- カバレッジの表示方法を切り替える関数
function M.toggle_display_method()
  local methods = { "inline", "signs", "highlight", "all" }
  local current_index = 1

  for i, method in ipairs(methods) do
    if method == M.config.display_method then
      current_index = i
      break
    end
  end

  -- 次の表示方法に切り替え
  current_index = (current_index % #methods) + 1
  M.config.display_method = methods[current_index]

  vim.notify("JaCoCo display method changed to: " .. M.config.display_method, vim.log.levels.INFO)

  -- カバレッジを再表示
  M.show()
end

-- カバレッジサマリーを表示する関数
function M.show_summary()
  -- JaCoCoレポートディレクトリを検索
  local report_dir = find_jacoco_report_dir()
  if not report_dir then
    vim.notify("No JaCoCo report directory found.", vim.log.levels.WARN)
    return
  end

  -- インデックスファイルの検索
  local index_file = report_dir .. "/index.html"
  if vim.fn.filereadable(index_file) ~= 1 then
    vim.notify("JaCoCo index file not found: " .. index_file, vim.log.levels.WARN)
    return
  end

  -- ファイルを読み込む
  local content = vim.fn.readfile(index_file)
  if not content or #content == 0 then
    vim.notify("Failed to read JaCoCo index file.", vim.log.levels.ERROR)
    return
  end

  -- カバレッジデータを抽出
  local summary = {
    instruction = { covered = 0, missed = 0, total = 0, percentage = 0 },
    branch = { covered = 0, missed = 0, total = 0, percentage = 0 },
    complexity = { covered = 0, missed = 0, total = 0, percentage = 0 },
    line = { covered = 0, missed = 0, total = 0, percentage = 0 },
    method = { covered = 0, missed = 0, total = 0, percentage = 0 },
    class = { covered = 0, missed = 0, total = 0, percentage = 0 },
    packages = {},
  }

  -- 全体のカバレッジデータを検索
  local total_found = false
  for _, line in ipairs(content) do
    -- tfoot内のカバレッジデータを検索
    if line:match("<tfoot>") then
      total_found = true
    elseif total_found and line:match("</tfoot>") then
      total_found = false
    end

    if total_found then
      -- 命令カバレッジ
      local instr_missed, instr_covered = line:match(
      'title="Instructions".-<td class="ctr2">(%d+)</td>.-<td class="ctr1">(%d+)</td>')
      if instr_missed and instr_covered then
        summary.instruction.missed = tonumber(instr_missed)
        summary.instruction.covered = tonumber(instr_covered)
        summary.instruction.total = summary.instruction.missed + summary.instruction.covered
        summary.instruction.percentage = math.floor((summary.instruction.covered / summary.instruction.total) * 100)
      end

      -- 分岐カバレッジ
      local branch_missed, branch_covered = line:match(
      'title="Branches".-<td class="ctr2">(%d+)</td>.-<td class="ctr1">(%d+)</td>')
      if branch_missed and branch_covered then
        summary.branch.missed = tonumber(branch_missed)
        summary.branch.covered = tonumber(branch_covered)
        summary.branch.total = summary.branch.missed + summary.branch.covered
        summary.branch.percentage = math.floor((summary.branch.covered / summary.branch.total) * 100)
      end

      -- 複雑度カバレッジ
      local complexity_missed, complexity_covered = line:match(
      'title="Complexity".-<td class="ctr2">(%d+)</td>.-<td class="ctr1">(%d+)</td>')
      if complexity_missed and complexity_covered then
        summary.complexity.missed = tonumber(complexity_missed)
        summary.complexity.covered = tonumber(complexity_covered)
        summary.complexity.total = summary.complexity.missed + summary.complexity.covered
        summary.complexity.percentage = math.floor((summary.complexity.covered / summary.complexity.total) * 100)
      end

      -- 行カバレッジ
      local line_missed, line_covered = line:match(
      'title="Lines".-<td class="ctr2">(%d+)</td>.-<td class="ctr1">(%d+)</td>')
      if line_missed and line_covered then
        summary.line.missed = tonumber(line_missed)
        summary.line.covered = tonumber(line_covered)
        summary.line.total = summary.line.missed + summary.line.covered
        summary.line.percentage = math.floor((summary.line.covered / summary.line.total) * 100)
      end

      -- メソッドカバレッジ
      local method_missed, method_covered = line:match(
      'title="Methods".-<td class="ctr2">(%d+)</td>.-<td class="ctr1">(%d+)</td>')
      if method_missed and method_covered then
        summary.method.missed = tonumber(method_missed)
        summary.method.covered = tonumber(method_covered)
        summary.method.total = summary.method.missed + summary.method.covered
        summary.method.percentage = math.floor((summary.method.covered / summary.method.total) * 100)
      end

      -- クラスカバレッジ
      local class_missed, class_covered = line:match(
      'title="Classes".-<td class="ctr2">(%d+)</td>.-<td class="ctr1">(%d+)</td>')
      if class_missed and class_covered then
        summary.class.missed = tonumber(class_missed)
        summary.class.covered = tonumber(class_covered)
        summary.class.total = summary.class.missed + summary.class.covered
        summary.class.percentage = math.floor((summary.class.covered / summary.class.total) * 100)
      end
    end
  end

  -- パッケージ別カバレッジを抽出
  local in_package_table = false
  local package_rows = {}

  for _, line in ipairs(content) do
    if line:match('<table id="packages">') then
      in_package_table = true
    elseif in_package_table and line:match('</table>') then
      in_package_table = false
    end

    if in_package_table and line:match('<tr>') then
      table.insert(package_rows, line)
    end
  end

  -- サマリー情報を整形して表示
  local summary_text = "JaCoCo Coverage Summary:\n\n"

  -- 全体のカバレッジ
  summary_text = summary_text .. "Overall Coverage:\n"
  summary_text = summary_text .. string.format("  Lines: %d%% (%d of %d)\n",
    summary.line.percentage, summary.line.covered, summary.line.total)
  summary_text = summary_text .. string.format("  Branches: %d%% (%d of %d)\n",
    summary.branch.percentage, summary.branch.covered, summary.branch.total)
  summary_text = summary_text .. string.format("  Methods: %d%% (%d of %d)\n",
    summary.method.percentage, summary.method.covered, summary.method.total)
  summary_text = summary_text .. string.format("  Classes: %d%% (%d of %d)\n",
    summary.class.percentage, summary.class.covered, summary.class.total)

  -- HTMLレポートへのリンク情報
  summary_text = summary_text .. "\nFull Report: " .. index_file .. "\n"
  summary_text = summary_text .. "Use ':lua require(\"jacoco\").open_report()' to open in browser"

  -- 結果を表示
  vim.notify(summary_text, vim.log.levels.INFO)

  -- ブラウザで開くかどうかを確認
  vim.ui.select({ "Open in browser", "Cancel" }, {
    prompt = "Do you want to open the full coverage report in browser?",
  }, function(choice)
    if choice == "Open in browser" then
      M.open_report()
    end
  end)

  return summary
end

-- プロジェクト全体のカバレッジレポートをブラウザで開く関数
function M.open_report()
  local report_dir = find_jacoco_report_dir()
  if not report_dir then
    vim.notify("No JaCoCo report directory found.", vim.log.levels.WARN)
    return
  end

  -- インデックスファイルの検索
  local index_file = report_dir .. "/index.html"
  if vim.fn.filereadable(index_file) ~= 1 then
    vim.notify("JaCoCo index file not found: " .. index_file, vim.log.levels.WARN)
    return
  end

  -- ブラウザで開く
  local cmd
  if vim.fn.has("mac") == 1 then
    cmd = "open " .. index_file
  elseif vim.fn.has("unix") == 1 then
    cmd = "xdg-open " .. index_file
  elseif vim.fn.has("win32") == 1 then
    cmd = "start " .. index_file
  else
    vim.notify("Unsupported platform for opening HTML report", vim.log.levels.ERROR)
    return
  end

  vim.fn.jobstart(cmd, {
    on_exit = function(_, code)
      if code ~= 0 then
        vim.notify("Failed to open HTML report: " .. index_file, vim.log.levels.ERROR)
      end
    end
  })

  vim.notify("Opening JaCoCo coverage report in browser: " .. index_file, vim.log.levels.INFO)
end

-- カバレッジ情報をフローティングウィンドウで表示する関数
function M.show_coverage_popup()
  local current_filename = vim.fn.expand("%:t")
  local html_report_path = find_jacoco_html_report(current_filename)

  if not html_report_path then
    vim.notify("No JaCoCo HTML report found for " .. current_filename, vim.log.levels.WARN)
    return
  end

  -- HTMLレポートを解析
  local coverage_data = parse_jacoco_html_report(html_report_path)
  if not coverage_data or vim.tbl_isempty(coverage_data) then
    vim.notify("Failed to parse JaCoCo HTML report.", vim.log.levels.ERROR)
    return
  end

  -- カバレッジの統計を計算
  local total_lines = vim.api.nvim_buf_line_count(0)
  local covered_lines = 0
  local missed_lines = 0
  local partial_lines = 0
  local instrumented_lines = 0

  for _, data in pairs(coverage_data) do
    instrumented_lines = instrumented_lines + 1
    if data.status == "covered" then
      covered_lines = covered_lines + 1
    elseif data.status == "missed" then
      missed_lines = missed_lines + 1
    elseif data.status == "partial" then
      partial_lines = partial_lines + 1
    end
  end

  local coverage_percent = 0
  if instrumented_lines > 0 then
    coverage_percent = math.floor((covered_lines / instrumented_lines) * 100)
  end

  -- 表示内容を作成
  local content = {
    "Coverage for " .. current_filename .. ":",
    "",
    "Line Coverage: " .. coverage_percent .. "% (" .. covered_lines .. " of " .. instrumented_lines .. ")",
    "  ✓ Covered:  " .. covered_lines .. " lines",
    "  ✗ Missed:   " .. missed_lines .. " lines",
    "  ◑ Partial:  " .. partial_lines .. " lines",
    "",
    "Total instrumented lines: " .. instrumented_lines .. " of " .. total_lines,
    "",
    "Press 'o' to open full HTML report"
  }

  -- フローティングウィンドウを作成
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, content)

  -- 表示場所を計算
  local width = 60
  local height = #content
  local win_height = vim.api.nvim_get_option("lines")
  local win_width = vim.api.nvim_get_option("columns")
  local row = math.floor((win_height - height) / 2)
  local col = math.floor((win_width - width) / 2)

  -- ウィンドウオプション
  local opts = {
    relative = "editor",
    row = row,
    col = col,
    width = width,
    height = height,
    style = "minimal",
    border = "rounded"
  }

  -- ウィンドウを表示
  local win = vim.api.nvim_open_win(buf, true, opts)

  -- 色設定
  vim.api.nvim_buf_add_highlight(buf, -1, "Title", 0, 0, -1)
  vim.api.nvim_buf_add_highlight(buf, -1, "Comment", 7, 0, -1)

  -- 'o'キーでHTMLレポートを開くキーマップ
  vim.api.nvim_buf_set_keymap(buf, "n", "o",
    "<cmd>lua require('jacoco').open_html_report()<CR><cmd>close<CR>",
    { noremap = true, silent = true }
  )

  -- 'q'キーで閉じるキーマップ
  vim.api.nvim_buf_set_keymap(buf, "n", "q", "<cmd>close<CR>",
    { noremap = true, silent = true }
  )

  -- バッファ設定
  vim.api.nvim_buf_set_option(buf, "modifiable", false)
  vim.api.nvim_buf_set_option(buf, "bufhidden", "wipe")

  -- ヘルプメッセージ
  vim.api.nvim_echo({ { "Press 'q' to close, 'o' to open HTML report", "Comment" } }, false, {})

  return win
end

return M

