# Testing Philosophy

テスト設計の思想とシニアエンジニアが守るべき原則。

## 核心思想

### 1. テストは仕様の文書化

テストは実行可能なドキュメントである。コードが「何をすべきか」を明確に示し、将来の変更に対するセーフティネットとなる。

```javascript
// BAD: テストの意図が不明確
test('test1', () => {
  const result = process(data)
  expect(result).toBe(42)
})

// GOOD: テストがビジネス要件を明確に文書化
test('顧客の最終注文日から30日以上経過している場合、リマインダーメールを送信する', () => {
  // Arrange
  const customer = {
    lastOrderDate: new Date('2023-01-01'),
    email: 'user@example.com'
  }
  const today = new Date('2023-02-15') // 45日後

  // Act
  const shouldSend = needsReminderEmail(customer, today)

  // Assert
  expect(shouldSend).toBe(true)
})
```

**なぜ重要か**: テストがビジネスロジックを明確に表現していれば、新しいチームメンバーはコードとテストを読むだけで要件を理解できる。コメントは腐るが、テストは常に最新の動作を保証する。

### 2. テストピラミッド vs テストトロフィー

#### テストピラミッド（従来型）

Mike Cohn、Martin Fowlerが提唱。高速な単体テストを土台に、統合テスト、E2Eテストと続く。

```
        /\
       /E2E\      10%  (遅い、不安定、高コスト)
      /------\
     / 統合   \    20%  (中速、実際の連携を検証)
    /----------\
   /   単体    \  70%  (高速、安定、低コスト)
  /--------------\
```

**推奨比率**: 単体 70% / 統合 20% / E2E 10%

**哲学**: 「すべてを隔離し、個別にテストする」

#### テストトロフィー（モダン）

Kent C. Doddsが提唱。統合テストを最重視し、実際の利用に近い形でテストする。

```
     ___
    | E2E |     少数  (クリティカルパスのみ)
   /-------\
  / 統合    \   最多  (コンポーネント間の連携)
 /-----------\
|   単体     |  少数  (複雑なロジックのみ)
|------------|
|静的解析    |  土台  (Linter, TypeScript)
 -------------
```

**哲学**: 「ユーザーが使う方法に近い形でテストする」

**どちらを選ぶべきか**:

| 状況 | 推奨 | 理由 |
|------|------|------|
| 複雑なアルゴリズム中心 | ピラミッド | 個別ロジックの正しさが重要 |
| モダンWebアプリ（React等） | トロフィー | コンポーネント間の連携が重要 |
| マイクロサービス | トロフィー | サービス間統合が最も脆弱 |
| レガシーシステム | ピラミッド | 既存の単体テストを活用 |

### 3. Arrange-Act-Assert（AAA Pattern）

テストを3つの明確なセクションに分割する構造化パターン。

```javascript
// BAD: 構造が不明瞭
test('getLatestOrder', () => {
  const customer = { orders: [...] }
  expect(getLatestOrder(customer)).toEqual(...)
  const result = getLatestOrder(customer)
  // どこまでがセットアップ?
})

// GOOD: AAA Pattern
test('最新の注文を日付順で取得する', () => {
  // Arrange（準備）: テストに必要なすべての前提条件
  const customer = {
    name: 'John Doe',
    orders: [
      { id: 1, date: new Date('2023-01-15'), amount: 100 },
      { id: 2, date: new Date('2023-03-20'), amount: 150 }, // 最新
      { id: 3, date: new Date('2023-02-10'), amount: 75 },
    ],
  }
  const expected = { id: 2, date: new Date('2023-03-20'), amount: 150 }

  // Act（実行）: テスト対象の関数を実行（通常1行）
  const result = getLatestOrder(customer)

  // Assert（検証）: 期待される結果と比較
  expect(result).toEqual(expected)
})
```

**BDDスタイル（Given-When-Then）**: AAAを自然言語で表現

```gherkin
# 同じ意図をGherkin構文で
Scenario: ATMで残高が十分な場合に現金を引き出す
  Given 口座残高が100ドル
  And カードが有効
  And ATMに十分な現金がある
  When 利用者が20ドルを要求
  Then ATMは20ドルを払い出す
  And 口座残高は80ドルになる
```

**なぜ重要か**: 構造が標準化されると、他の開発者がテストの意図を即座に理解できる。テストが失敗したとき、問題が前提条件・実行・検証のどこにあるか特定しやすい。

### 4. テストの独立性と再現性

各テストは他のテストから完全に独立し、どの順序で実行しても同じ結果を返すべき。

```javascript
// BAD: テスト間で状態を共有（順序依存）
let user // グローバル状態

test('ユーザー作成', () => {
  user = createUser('Alice')
  expect(user.name).toBe('Alice')
})

test('ユーザー更新', () => {
  user.age = 30 // 前のテストに依存
  expect(user.age).toBe(30)
})

// GOOD: 各テストが完全に独立
test('ユーザー作成', () => {
  const user = createUser('Alice')
  expect(user.name).toBe('Alice')
})

test('ユーザー更新', () => {
  // 必要な状態をこのテスト内で構築
  const user = createUser('Bob')
  user.age = 30
  expect(user.age).toBe(30)
})
```

```javascript
// BAD: 非決定論的（時刻に依存）
test('今日の日付をフォーマット', () => {
  const result = formatToday()
  expect(result).toBe('2023-03-20') // 明日は失敗
})

// GOOD: 時刻を注入可能に
test('指定日付をフォーマット', () => {
  const fixedDate = new Date('2023-03-20')
  const result = formatDate(fixedDate)
  expect(result).toBe('2023-03-20')
})
```

**なぜ重要か**: フレーキー（不安定）なテストは開発者の信頼を失わせる。「またあのテストが落ちた」と無視されるようになり、本当のバグを見逃すリスクが高まる。

## テストダブルの使い分け

Martin Fowlerによって定義されたテストダブルの種類と選択基準。

### 状態検証 vs 振る舞い検証

| タイプ | 用途 | 検証内容 | 使用例 |
|--------|------|----------|--------|
| **Dummy** | プレースホルダー | 何も検証しない | `new Service(dummyLogger, dummyConfig)` |
| **Fake** | 簡易実装 | 状態検証 | インメモリDB、ローカルストレージ |
| **Stub** | 固定値を返す | 状態検証 | `api.get.returns({ status: 200 })` |
| **Spy** | 呼び出しを記録 | 振る舞い検証 | `jest.spyOn(obj, 'method')` |
| **Mock** | 期待を事前定義 | 振る舞い検証 | `expect(mock).toHaveBeenCalledWith(...)` |

### 具体例

```javascript
// Dummy: 単にそこに存在するだけ
const dummyLogger = { log: () => {} }
new EmailService(emailClient, dummyLogger)

// Fake: 動作する軽量実装
class FakeDatabase {
  constructor() { this.data = new Map() }
  save(key, value) { this.data.set(key, value) }
  get(key) { return this.data.get(key) }
}

// Stub: 固定値を返すことで実行経路を制御
const apiStub = {
  fetchUser: jest.fn().mockResolvedValue({ id: 1, name: 'Alice' })
}

// Spy: 本物を監視
const realService = new PaymentService()
const processSpy = jest.spyOn(realService, 'processPayment')
// ... 実行後
expect(processSpy).toHaveBeenCalledTimes(1)

// Mock: 期待を事前に定義
const mockEmailClient = {
  send: jest.fn()
}
await notifyUser(mockEmailClient, 'user@example.com')
expect(mockEmailClient.send).toHaveBeenCalledWith(
  'user@example.com',
  expect.stringContaining('Welcome')
)
```

**選択基準**:

- **状態をテストする** → Stub/Fake を使う
  - 「この関数がXを返したら、Yになるか?」
- **振る舞いをテストする** → Mock/Spy を使う
  - 「この関数がXというメソッドを正しい引数で呼んだか?」

## アンチパターン

### 過剰なモック（AIがやりがち）

すべての依存関係をモックで置き換えてしまう。

```javascript
// BAD: すべてをモック（実装詳細に密結合）
test('ユーザー登録', () => {
  const mockValidator = { validate: jest.fn().mockReturnValue(true) }
  const mockHasher = { hash: jest.fn().mockReturnValue('hashed') }
  const mockDb = { save: jest.fn().mockResolvedValue({ id: 1 }) }
  const mockMailer = { send: jest.fn() }

  const service = new UserService(mockValidator, mockHasher, mockDb, mockMailer)
  await service.register({ email: 'a@b.com', password: 'pass' })

  // 内部の呼び出し順序を検証（脆い）
  expect(mockValidator.validate).toHaveBeenCalledFirst()
  expect(mockHasher.hash).toHaveBeenCalledAfter(mockValidator.validate)
  // リファクタリングで順序が変わると壊れる
})

// GOOD: 本物を使うか、統合テストに昇格
test('ユーザー登録の統合テスト', async () => {
  const testDb = new InMemoryDatabase() // Fake
  const service = new UserService(
    new RealValidator(),
    new RealHasher(),
    testDb,
    new FakeMailer()
  )

  const user = await service.register({ email: 'a@b.com', password: 'pass' })

  // 最終的な状態を検証（実装に非依存）
  expect(user.email).toBe('a@b.com')
  expect(user.passwordHash).toBeTruthy()
  expect(testDb.users.size).toBe(1)
})
```

**なぜ問題か**:
- リファクタリング不能: 内部実装を変えるとテストが壊れる
- 偽の安心感: モックは本物の振る舞いを保証しない
- 設計問題の隠蔽: モックが大量に必要=責務が多すぎる可能性

### 実装詳細のテスト

公開APIではなく、内部実装をテストする。

```javascript
// BAD: privateメソッドをテスト
class ShoppingCart {
  #calculateSubtotal(items) { /* ... */ }
  #applyDiscount(subtotal) { /* ... */ }

  getTotal(items) {
    const subtotal = this.#calculateSubtotal(items)
    return this.#applyDiscount(subtotal)
  }
}

// これは内部実装のテスト（アンチパターン）
test('calculateSubtotal', () => {
  const cart = new ShoppingCart()
  // privateメソッドを無理やりテスト
  expect(cart['#calculateSubtotal']([...])).toBe(100)
})

// GOOD: 公開された振る舞いをテスト
test('商品合計が10000円以上で10%割引が適用される', () => {
  const cart = new ShoppingCart()
  const items = [
    { price: 5000, quantity: 2 },
    { price: 2000, quantity: 1 }
  ]

  const total = cart.getTotal(items) // 公開API

  expect(total).toBe(10800) // 12000 * 0.9
})
```

**なぜ問題か**: 内部実装を変更（例: `calculateSubtotal`を`computeSum`にリネーム）しただけで、外部の振る舞いが同じでもテストが壊れる。

### フレーキーテスト（不安定なテスト）

実行ごとに結果が変わるテスト。

```javascript
// BAD: 固定待機（環境依存で不安定）
test('データ取得', async () => {
  fetchData()
  await sleep(1000) // 環境が遅いと1秒では足りない
  expect(data).toBeDefined()
})

// GOOD: 完了を待つ
test('データ取得', async () => {
  const data = await fetchData() // Promiseの完了を待つ
  expect(data).toBeDefined()
})
```

```javascript
// BAD: 現在時刻に依存
test('キャンペーン期間中か判定', () => {
  const isActive = isCampaignActive()
  expect(isActive).toBe(true) // 期間外になると失敗
})

// GOOD: 時刻を注入
test('キャンペーン期間中か判定', () => {
  const now = new Date('2023-12-25T10:00:00Z')
  const isActive = isCampaignActive(now)
  expect(isActive).toBe(true)
})
```

**なぜ問題か**: フレーキーテストはCI/CDを頻繁に止め、開発者がテスト結果を信頼しなくなる。

## シニアエンジニアの判断基準

### テスト種別の選択

| ケース | 推奨 | 理由 |
|--------|------|------|
| 複雑な計算ロジック | 単体テスト | 高速にエッジケースを網羅 |
| 純粋関数 | 単体テスト | 同じ入力→同じ出力を保証 |
| API呼び出し | 統合テスト | 実際の通信を検証 |
| DB操作 | 統合テスト | データ永続化を確認 |
| Reactコンポーネント | 統合テスト | ユーザー操作をシミュレート |
| ログイン→購入フロー | E2E | ビジネス上のクリティカルパス |
| 型エラー・構文エラー | 静的解析 | 最も高速・低コスト |

### テストカバレッジの正しい解釈

**100%カバレッジは目標ではない**

```javascript
// カバレッジ100%でも意味のないテスト
function add(a, b) {
  return a + b
}

test('add', () => {
  add(1, 2) // 実行されたが、検証なし
  // カバレッジ100%だが、正しさは未検証
})
```

**カバレッジの正しい使い方**:
- ✅ 未テストの重要領域を発見するツール
- ✅ カバレッジの低下を検知する指標
- ❌ チーム目標（「90%を目指す」等）
- ❌ テスト品質の指標

**Martin Fowlerの見解**:
> "Test coverage is a useful tool for finding untested parts of a codebase. Test coverage is of little use as a numeric statement of how good your tests are."

### TDD（Test-Driven Development）の3つの法則

Kent Beckが提唱するRed-Green-Refactorサイクル。

1. **失敗するテストを書くまで、プロダクションコードを書いてはいけない**
2. **失敗する最小限のテストだけを書く（コンパイルエラーも失敗）**
3. **1つのテストをパスする最小限のコードだけを書く**

```javascript
// 1. Red: 失敗するテストを書く
test('空のカートの合計は0', () => {
  const cart = new ShoppingCart() // まだ存在しない
  expect(cart.getTotal()).toBe(0)
})

// 2. Green: テストをパスする最小限のコード
class ShoppingCart {
  getTotal() { return 0 } // ハードコードでOK
}

// 3. Refactor: テストを追加し、実装を改善
test('商品を追加すると合計が更新される', () => {
  const cart = new ShoppingCart()
  cart.addItem({ price: 100 })
  expect(cart.getTotal()).toBe(100)
})

// リファクタリング: 実際のロジックを実装
class ShoppingCart {
  constructor() { this.items = [] }
  addItem(item) { this.items.push(item) }
  getTotal() { return this.items.reduce((sum, i) => sum + i.price, 0) }
}
```

### BDD vs TDD

| | TDD | BDD |
|---|-----|-----|
| **焦点** | 実装の正しさ | ビジネス要件の充足 |
| **対象者** | 開発者 | 開発者+QA+ビジネス |
| **言語** | プログラミング言語 | 自然言語（Gherkin） |
| **粒度** | 関数・クラス | ユーザーストーリー |
| **哲学** | "正しく作る" | "正しいものを作る" |

## 参考資料

### 基本思想
- [Martin Fowler - The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Kent C. Dodds - The Testing Trophy](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)
- [Kent C. Dodds - Write tests. Not too many. Mostly integration.](https://kentcdodds.com/blog/write-tests)

### テストダブル
- [Martin Fowler - TestDouble](https://martinfowler.com/bliki/TestDouble.html)
- [Martin Fowler - Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html)

### TDD/BDD
- [Robert C. Martin - The Three Laws of TDD](https://blog.cleancoder.com/uncle-bob/2014/12/17/TheCyclesOfTDD.html)
- [Cucumber - Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)
- [Martin Fowler - GivenWhenThen](https://martinfowler.com/bliki/GivenWhenThen.html)

### アンチパターン
- [Kent C. Dodds - Testing Implementation Details](https://kentcdodds.com/blog/testing-implementation-details)
- [Martin Fowler - TestCoverage](https://martinfowler.com/bliki/TestCoverage.html)
