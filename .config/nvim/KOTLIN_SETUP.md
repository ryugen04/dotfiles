# Kotlin開発環境セットアップガイド

JetBrains公式kotlin-lspをベースとした、Neovim Kotlin開発環境のセットアップ手順です。

## 概要

この設定では以下の機能を提供します：

- **LSP**: JetBrains公式kotlin-lspによる補完、診断、リファクタリング
- **フォーマット**: ktlint（IntelliJ IDEA準拠）
- **静的解析**: Detekt（リアルタイム診断 + Gradle統合）
- **テスト**: neotest-kotlin（Kotest対応）
- **デバッグ**: nvim-dap + kotlin-debug-adapter

### 制限事項

JetBrains公式kotlin-lspは現在プレアルファ段階で、以下の機能が**サポートされていません**：

- ❌ Type Definition（型定義へジャンプ）- `textDocument/typeDefinition`
- ❌ Go to Implementation（実装へジャンプ）- `textDocument/implementation`
- ❌ Go to Declaration（宣言へジャンプ）- `textDocument/declaration`

これらの機能については、**Treesitterベースの代替実装**を提供しています。詳細は「[8. 機能制限と代替実装](#8-機能制限と代替実装)」を参照してください。

## 1. 必要なツールのインストール

### 1.1 JetBrains公式kotlin-lsp

JetBrains公式のKotlin Language Serverをインストールします。

```bash
# Homebrewでインストール
brew install JetBrains/utils/kotlin-lsp

# インストール確認
kotlin-lsp --version
```

**注意**:
- JetBrains公式kotlin-lspはまだプレアルファ段階です。安定性を重視する場合は、fwcd版の使用も検討してください。
- kotlin-lspは`--stdio`オプションで起動されます（デフォルトはTCPモード：ポート9999）

### 1.2 ktlint（Masonでインストール）

Neovimを起動して、Masonでktlintをインストールします。

```vim
:Mason
```

Masonウィンドウで以下を検索してインストール：
- `ktlint` - Kotlinフォーマッタ/リンター

または、コマンドで直接インストール：

```vim
:MasonInstall ktlint
```

### 1.3 kotlin-debug-adapter（Masonでインストール）

デバッグ機能を使用する場合は、kotlin-debug-adapterもインストールします。

```vim
:MasonInstall kotlin-debug-adapter
```

### 1.4 Gradleプラグイン（プロジェクト側の設定）

プロジェクトの`build.gradle.kts`にDetektとktlintプラグインを追加します。

```kotlin
plugins {
    kotlin("jvm") version "1.9.20"
    id("io.gitlab.arturbosch.detekt") version "1.23.4"
    id("org.jlleitschuh.gradle.ktlint") version "12.0.3"
}

// Detekt設定
detekt {
    buildUponDefaultConfig = true
    allRules = false
    config.setFrom("$projectDir/config/detekt.yml")
}

// ktlint設定（IntelliJ IDEA準拠）
ktlint {
    version.set("1.1.0")
    android.set(false)
    ignoreFailures.set(false)
    enableExperimentalRules.set(true)
}

dependencies {
    detektPlugins("io.gitlab.arturbosch.detekt:detekt-formatting:1.23.4")
}
```

## 2. Neovim設定の確認

### 2.1 設定ファイルの確認

以下のファイルが正しく配置されているか確認します：

```
~/.config/nvim/
├── lua/plugins/configs/
│   ├── lang/
│   │   └── kotlin.lua          # 新規作成
│   └── coding/
│       ├── mason.lua            # 修正済み
│       └── format.lua           # 修正済み
```

### 2.2 Neovimプラグインの同期

Neovimを起動して、プラグインを同期します。

```vim
:Lazy sync
```

以下のプラグインが自動的にインストールされます：
- `udalov/kotlin-vim` - シンタックスハイライト
- `codymikol/neotest-kotlin` - Kotestテスト実行（test.luaで統合済み）
- `Mgenuit/nvim-dap-kotlin` - デバッグ機能

**注意**: neotest-kotlinアダプタは`test.lua`で既に設定されています。JavaとKotlinの両方のテストをサポートします。

## 3. プロジェクトセットアップ

### 3.1 .editorconfigのコピー

dotfilesディレクトリのサンプルをプロジェクトルートにコピーします。

```bash
# dotfilesディレクトリから
cd /path/to/your/kotlin/project
cp ~/.config/dotfiles/.editorconfig.kotlin-example .editorconfig
```

### 3.2 Detekt設定ファイル

プロジェクトルートに`config/detekt.yml`を作成します（任意）。

```bash
mkdir -p config
touch config/detekt.yml
```

基本的な`detekt.yml`の例：

```yaml
build:
  maxIssues: 0
  excludeCorrectable: false

config:
  validation: true
  warningsAsErrors: false

style:
  MaxLineLength:
    maxLineLength: 120
    excludeCommentStatements: true

  TrailingWhitespace:
    active: true

  FinalNewline:
    active: true

complexity:
  ComplexMethod:
    threshold: 15

  LongMethod:
    threshold: 60

  LongParameterList:
    functionThreshold: 6
    constructorThreshold: 7
```

### 3.3 Gradle Wrapperの確認

プロジェクトルートに`gradlew`が存在することを確認します。

```bash
# プロジェクトルートで
./gradlew --version
```

## 4. 利用可能な機能とキーマップ

### 4.1 LSP機能（kotlin.lua:75-88）

| キーマップ | 機能 | 説明 |
|-----------|------|------|
| `gd` | 定義へジャンプ | カーソル位置のシンボル定義へ移動 |
| `gr` | 参照検索 | シンボルの全参照箇所を表示 |
| `K` | ホバー情報 | 型情報やドキュメントを表示 |
| `<leader>rn` | リネーム | シンボル名を一括変更 |
| `<leader>ca` | コードアクション | クイックフィックス/リファクタリング |
| `<leader>e` | 診断を表示 | エラー/警告の詳細を表示 |
| `[d` | 前の診断へ | 前のエラー/警告へ移動 |
| `]d` | 次の診断へ | 次のエラー/警告へ移動 |
| `<leader>lf` | フォーマット | LSP経由でフォーマット |

### 4.2 テスト実行（kotlin.lua:155-167）

| キーマップ | 機能 | 説明 |
|-----------|------|------|
| `<leader>tn` | 最寄りのテスト実行 | カーソル位置のテストを実行 |
| `<leader>tf` | ファイル内テスト実行 | 現在のファイルの全テストを実行 |
| `<leader>ts` | テストサマリー表示 | テスト結果サマリーをトグル |
| `<leader>to` | テスト出力表示 | テスト実行結果の詳細を表示 |

### 4.3 デバッグ（kotlin.lua:211-227）

| キーマップ | 機能 | 説明 |
|-----------|------|------|
| `<leader>db` | ブレークポイント | ブレークポイントをトグル |
| `<leader>dc` | デバッグ続行 | デバッグセッションを続行 |
| `<leader>ds` | ステップオーバー | 次の行へステップ |
| `<leader>di` | ステップイン | 関数内へステップ |

### 4.4 Gradle統合（kotlin.lua:234-264）

| キーマップ | 機能 | 説明 |
|-----------|------|------|
| `<leader>kg` | Gradleタスク選択 | タスク一覧から選択実行 |
| `<leader>kd` | Detekt実行 | 静的解析を実行 |
| `<leader>kf` | ktlintフォーマット | Gradle経由でフォーマット |

### 4.5 自動フォーマット/リント

- **保存時自動フォーマット**: ktlintでIntelliJ IDEA準拠のフォーマット
- **リアルタイム診断**: ktlint（常時） + Detekt（保存時）

無効化する場合：

```vim
" 保存時フォーマットを無効化
:w!

" または、設定で無効化（~/.config/nvim/lua/plugins/configs/coding/format.lua）
format_on_save = nil
```

## 5. 動作確認

### 5.1 LSPの起動確認

Kotlinファイルを開いて、LSPが起動しているか確認します。

```vim
:LspInfo
```

`kotlin_lsp`が`Attached`と表示されればOKです。

### 5.2 補完の確認

Kotlinファイルで`println`と入力し、補完が表示されることを確認します。

### 5.3 診断の確認

意図的に構文エラーを作成し、診断が表示されることを確認します。

```kotlin
fun test() {
    val x: Int = "string" // 型エラーが表示されるはず
}
```

### 5.4 フォーマットの確認

フォーマットが乱れたコードを作成し、保存時に自動整形されることを確認します。

```kotlin
fun    test(  )   {
println(    "test"   )
}
```

保存すると以下のように整形されます：

```kotlin
fun test() {
    println("test")
}
```

### 5.5 テスト実行の確認

Kotestのテストファイルを作成し、`<leader>tn`でテストを実行します。

```kotlin
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.shouldBe

class ExampleTest : FunSpec({
    test("example test") {
        1 + 1 shouldBe 2
    }
})
```

## 6. トラブルシューティング

### 6.1 kotlin-lspが起動しない

**症状**: `:LspInfo`で`kotlin_lsp`が表示されない

**解決策**:

1. kotlin-lspがインストールされているか確認

```bash
which kotlin-lsp
```

2. Homebrewで再インストール

```bash
brew reinstall JetBrains/utils/kotlin-lsp
```

3. Neovimを再起動

### 6.1.1 Address already in useエラー

**症状**: LSPログに`java.net.BindException: Address already in use`が表示される

**原因**: kotlin-lspプロセスが既に実行中、または`--stdio`オプションが設定されていない

**解決策**:

1. 既存のkotlin-lspプロセスを終了

```bash
pkill -f kotlin-lsp
```

2. kotlin.luaで`--stdio`オプションが設定されているか確認

```lua
-- kotlin.lua:18
cmd = { 'kotlin-lsp', '--stdio' },
```

3. Neovimを再起動してKotlinファイルを開く

### 6.2 Detektが動作しない

**症状**: 保存してもDetektの診断が表示されない

**解決策**:

1. Gradleでdetektタスクが存在するか確認

```bash
./gradlew tasks --all | grep detekt
```

2. build.gradle.ktsにdetektプラグインが追加されているか確認

3. 手動でdetektを実行して出力を確認

```bash
./gradlew detekt
```

4. nvim-lintのログを確認

```vim
:lua vim.print(require('lint')._resolve_linter_by_ft('kotlin'))
```

### 6.3 テストが実行されない

**症状**: `<leader>tn`でテストが実行されない

**解決策**:

1. neotest-kotlinがtest.luaで正しく設定されているか確認

```lua
-- test.lua:46-47
-- Kotlin/Kotest用アダプタ
require("neotest-kotlin")
```

2. neotest-kotlinがインストールされているか確認

```vim
:Lazy
```

3. Kotestがプロジェクトの依存関係に含まれているか確認

```kotlin
// build.gradle.kts
dependencies {
    testImplementation("io.kotest:kotest-runner-junit5:5.8.0")
    testImplementation("io.kotest:kotest-assertions-core:5.8.0")
}

tasks.withType<Test> {
    useJUnitPlatform()
}
```

3. neotestのログを確認

```vim
:Neotest output-panel
```

### 6.4 フォーマットが適用されない

**症状**: 保存してもコードが整形されない

**解決策**:

1. ktlintがインストールされているか確認

```vim
:Mason
```

2. conform.nvimの設定を確認

```vim
:lua vim.print(require('conform').list_formatters())
```

3. 手動でフォーマットを実行

```vim
:lua require('conform').format()
```

### 6.5 デバッグが開始されない

**症状**: `<leader>dc`でデバッグが開始されない

**解決策**:

1. kotlin-debug-adapterがインストールされているか確認

```bash
which kotlin-debug-adapter
```

2. DAP設定を確認

```vim
:lua vim.print(require('dap').configurations.kotlin)
```

3. mainClassを正しく入力しているか確認（パッケージ名を含む）

```
例: com.example.MainKt
```

## 7. パフォーマンス最適化

### 7.1 Detektの実行頻度を調整

Detektは重い処理のため、保存時のみ実行されています。さらに頻度を下げる場合は、`format.lua`を編集します。

```lua
-- format.lua:172-179
-- Detektを手動実行のみにする場合
kotlin = { 'ktlint' }, -- detektを削除
```

### 7.2 LSPログレベルの調整

デバッグ情報が不要な場合は、LSPログレベルを下げます。

```lua
-- kotlin.lua に追加
vim.lsp.set_log_level("WARN")
```

## 8. 参考リンク

### 公式ドキュメント

- [JetBrains Kotlin LSP](https://github.com/Kotlin/kotlin-lsp)
- [ktlint](https://pinterest.github.io/ktlint/)
- [Detekt](https://detekt.dev/)
- [Kotest](https://kotest.io/)
- [neotest-kotlin](https://github.com/codymikol/neotest-kotlin)

### Neovimプラグイン

- [nvim-lspconfig](https://github.com/neovim/nvim-lspconfig)
- [conform.nvim](https://github.com/stevearc/conform.nvim)
- [nvim-lint](https://github.com/mfussenegger/nvim-lint)
- [neotest](https://github.com/nvim-neotest/neotest)
- [nvim-dap](https://github.com/mfussenegger/nvim-dap)

### コミュニティ

- [Kotlin Slack](https://surveys.jetbrains.com/s3/kotlin-slack-sign-up)
- [r/Kotlin](https://www.reddit.com/r/Kotlin/)
- [Neovim Discourse](https://neovim.discourse.group/)

---

## よくある質問

**Q: JetBrains公式kotlin-lspとfwcd版の違いは？**

A: JetBrains公式版はIntelliJ IDEAベースで最新機能がありますが、プレアルファ段階です。fwcd版は非推奨ですが、安定しています。プロダクション環境では安定性を重視してfwcd版を検討してください。

**Q: Detektの設定ファイルはどこに配置すべきですか？**

A: プロジェクトルートの`config/detekt.yml`に配置します。build.gradle.ktsで参照するパスと一致させてください。

**Q: IntelliJ IDEAと同じフォーマット結果になりますか？**

A: ktlintをIntelliJ IDEAコードスタイルで使用し、.editorconfigで設定することで、ほぼ同等の結果が得られます。完全に一致させるには、IntelliJ IDEAのエクスポート機能を使用してください。

**Q: Gradleのビルドが遅い場合の対処法は？**

A: Gradle Daemonを有効化し、`~/.gradle/gradle.properties`に以下を追加します：

```properties
org.gradle.daemon=true
org.gradle.parallel=true
org.gradle.caching=true
```

**Q: Kotestで特定のSpecが実行されない場合は？**

A: neotest-kotlinは主要なSpecをサポートしていますが、BehaviorSpecは未対応です。サポート状況は[neotest-kotlin README](https://github.com/codymikol/neotest-kotlin#supported-frameworks)を確認してください。

---

セットアップに関する質問や問題が発生した場合は、各プロジェクトのIssueトラッカーで報告してください。
