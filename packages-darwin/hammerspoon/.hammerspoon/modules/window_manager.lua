local window_management = {}

-- アクティブウィンドウを画面の左半分に移動する関数
function window_management.moveWindowLeft()
  local win = hs.window.focusedWindow()
  if win then
    win:moveToUnit(hs.layout.left50)
  end
end

-- アクティブウィンドウを画面の右半分に移動する関数
function window_management.moveWindowRight()
  local win = hs.window.focusedWindow()
  if win then
    win:moveToUnit(hs.layout.right50)
  end
end

-- アクティブウィンドウを画面の最大化する
function window_management.maximizeWindow()
  local win = hs.window.focusedWindow()
  if win then
    win:maximize()
  end
end

-- アクティブウィンドウを画面の最小化する
function window_management.minimizeWindow()
  local win = hs.window.focusedWindow()
  if win then
    local app = win:application()
    app:hide()
  end
end

-- アクティブウィンドウを次のスクリーンに移動
function window_management.moveWindowNextScreen()
  local win = hs.window.focusedWindow()
  if win then
    local nextScreen = win:screen():next()
    win:moveToScreen(nextScreen, true, true)
  end
end

-- アクティブウィンドウを前のスクリーンに移動
function window_management.moveWindowPrevScreen()
  local win = hs.window.focusedWindow()
  if win then
    local prevScreen = win:screen():previous()
    win:moveToScreen(prevScreen, true, true)
  end
end

return window_management

