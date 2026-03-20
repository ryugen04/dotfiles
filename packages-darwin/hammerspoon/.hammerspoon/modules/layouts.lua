local layouts = {}

-- レイアウト対象外のアプリを非表示にしない除外リスト
local SYSTEM_APPS = {
  ["Finder"] = true,
  ["Hammerspoon"] = true,
  ["Raycast"] = true,
  ["VoiceInk"] = true,
  ["設定"] = true,
  ["System Settings"] = true,
}

-- スクリーン取得ヘルパー
local function getScreens()
  local primary = hs.screen.primaryScreen()
  local allScreens = hs.screen.allScreens()
  local external = nil
  for _, s in ipairs(allScreens) do
    if s ~= primary then
      external = s
      break
    end
  end
  return primary, external
end

-- hs.layout.apply 用のエントリを作成
local function entry(appName, screen, unitRect)
  return { appName, nil, screen, unitRect, nil, nil }
end

-- レイアウト対象以外のアプリを非表示にする
local function hideOtherApps(targetApps)
  local targetSet = {}
  for _, name in ipairs(targetApps) do
    targetSet[name] = true
  end

  local runningApps = hs.application.runningApplications()
  for _, app in ipairs(runningApps) do
    local name = app:name()
    if name and not targetSet[name] and not SYSTEM_APPS[name] then
      if app:kind() == 1 then
        app:hide()
      end
    end
  end
end

-- レイアウト適用の共通処理
local function applyLayout(layoutDef, targetApps, layoutName)
  local main, ext = getScreens()
  if not ext then
    hs.alert.show("拡張ディスプレイが見つかりません")
    return
  end

  hideOtherApps(targetApps)

  for _, name in ipairs(targetApps) do
    local app = hs.application.get(name)
    if app then
      app:unhide()
    end
  end

  local layout = layoutDef(main, ext)
  hs.layout.apply(layout)

  hs.alert.show("Layout: " .. layoutName)
end

-- =============================================================
-- レイアウト定義
-- 拡張（上）= 主要な視線先、メイン（下）= サブ
-- =============================================================

--- coding: プログラミング
-- 拡張: cmux全画面
-- メイン: zen左1/2 + linear右1/2
function layouts.coding()
  applyLayout(function(main, ext)
    return {
      entry("cmux",   ext,  hs.layout.maximized),
      entry("Zen",    main, hs.layout.left50),
      entry("Linear", main, hs.layout.right50),
    }
  end, { "cmux", "Zen", "Linear" }, "coding")
end

--- verify: 動作確認
-- 拡張: cmux左1/2 + chrome右1/2
-- メイン: zen左1/2 + slack右1/2
function layouts.verify()
  applyLayout(function(main, ext)
    return {
      entry("cmux",          ext,  hs.layout.left50),
      entry("Google Chrome", ext,  hs.layout.right50),
      entry("Zen",           main, hs.layout.left50),
      entry("Slack",         main, hs.layout.right50),
    }
  end, { "cmux", "Google Chrome", "Zen", "Slack" }, "verify")
end

--- comms: コミュニケーション
-- 拡張: slack左1/2 + zen右1/2
-- メイン: linear左1/2 + cmux右1/2
function layouts.comms()
  applyLayout(function(main, ext)
    return {
      entry("Slack",  ext,  hs.layout.left50),
      entry("Zen",    ext,  hs.layout.right50),
      entry("Linear", main, hs.layout.left50),
      entry("cmux",   main, hs.layout.right50),
    }
  end, { "Slack", "Zen", "Linear", "cmux" }, "comms")
end

--- meeting: 会議
-- 拡張: chrome(空ウィンドウ)左1/2 + cmux右1/2
-- メイン: slack左3/4 + zen右2/3（重なり、slackが前面）
function layouts.meeting()
  local main, ext = getScreens()
  if not ext then
    hs.alert.show("拡張ディスプレイが見つかりません")
    return
  end

  -- 対象外アプリを非表示
  hideOtherApps({ "cmux", "Google Chrome", "Zen", "Slack" })

  -- 対象アプリを表示
  for _, name in ipairs({ "cmux", "Zen", "Slack" }) do
    local app = hs.application.get(name)
    if app then app:unhide() end
  end

  -- ChromeでGoogle Meetを開く
  local chrome = hs.application.get("Google Chrome")
  local beforeIds = {}
  if chrome then
    for _, w in ipairs(chrome:allWindows()) do
      beforeIds[w:id()] = true
    end
  end
  hs.execute("open -na 'Google Chrome' --args --new-window 'https://meet.google.com/landing'", true)

  -- 新規ウィンドウの出現を待つ（最大3秒）
  local chromeWin = nil
  for _ = 1, 30 do
    hs.timer.usleep(100000)
    chrome = hs.application.get("Google Chrome")
    if chrome then
      for _, w in ipairs(chrome:allWindows()) do
        if w:isStandard() and not beforeIds[w:id()] then
          chromeWin = w
          break
        end
      end
    end
    if chromeWin then break end
  end

  -- chrome空ウィンドウ → 拡張左1/2
  if chromeWin then
    chromeWin:moveToScreen(ext, false, false, 0)
    chromeWin:moveToUnit(hs.layout.left50)
  end

  -- cmux → 拡張右1/2
  hs.layout.apply({
    entry("cmux", ext, hs.layout.right50),
  })

  -- zen → メイン右2/3, slack → メイン左3/4
  hs.layout.apply({
    entry("Zen",   main, { 1/3, 0, 2/3, 1 }),
    entry("Slack", main, { 0, 0, 3/4, 1 }),
  })

  -- slackを前面に出す（重なり部分でslackが上）
  local slackApp = hs.application.get("Slack")
  if slackApp and slackApp:mainWindow() then
    slackApp:mainWindow():raise()
  end

  hs.alert.show("Layout: meeting")
end

--- linear: Linear作業
-- 拡張: linear左2/3 + zen右2/3（重なり、linearが前面）
-- メイン: slack左1/2 + cmux右1/2
function layouts.linear()
  applyLayout(function(main, ext)
    return {
      entry("Zen",    ext,  { 1/3, 0, 2/3, 1 }),
      entry("Linear", ext,  { 0, 0, 2/3, 1 }),
      entry("Slack",  main, hs.layout.left50),
      entry("cmux",   main, hs.layout.right50),
    }
  end, { "Linear", "Zen", "Slack", "cmux" }, "linear")

  -- linearを前面に出す
  local linearApp = hs.application.get("Linear")
  if linearApp and linearApp:mainWindow() then
    linearApp:mainWindow():raise()
  end
end

--- browser: ブラウザ作業
-- 拡張: zen左2/3 + linear右2/3（重なり、zenが前面）
-- メイン: slack左1/2 + cmux右1/2
function layouts.browser()
  applyLayout(function(main, ext)
    return {
      entry("Linear", ext,  { 1/3, 0, 2/3, 1 }),
      entry("Zen",    ext,  { 0, 0, 2/3, 1 }),
      entry("Slack",  main, hs.layout.left50),
      entry("cmux",   main, hs.layout.right50),
    }
  end, { "Zen", "Linear", "Slack", "cmux" }, "browser")

  -- zenを前面に出す
  local zenApp = hs.application.get("Zen")
  if zenApp and zenApp:mainWindow() then
    zenApp:mainWindow():raise()
  end
end

return layouts
