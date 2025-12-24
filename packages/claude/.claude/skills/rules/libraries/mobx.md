# MobX Philosophy

MobX の設計思想とシニアエンジニアが守るべき原則。

## 核心思想

### 1. TFRP (Transparent Functional Reactive Programming)

MobXの設計哲学の中心。スプレッドシートのような自動更新を実現する。

- **Transparent（透明性）**: 依存関係を明示的に定義しなくても、MobXが自動で依存グラフを構築する
- **Functional（関数的）**: 純粋関数で状態から新しい値を導出する（`computed`）
- **Reactive（反応的）**: 状態が変わると、依存するすべての導出値・副作用が自動で再実行される

```tsx
// MobXは「スプレッドシート」のように動く
// A1セルを変えると、=A1*2 のセルが自動更新されるのと同じ
class Store {
  @observable price = 100

  // priceが変わると自動で再計算（スプレッドシートの数式のように）
  @computed get priceWithTax() {
    return this.price * 1.1
  }
}
```

**なぜ重要か**: 開発者は単純に `user.name = "John"` のように書くだけで、UIや他の依存箇所の同期をMobXが自動で行う。購読・非購読の管理が不要。

### 2. Observable State（監視可能な状態）

状態を「観測可能」にすることで、変更を自動追跡する。

```tsx
import { makeAutoObservable } from "mobx"

// GOOD: makeAutoObservableで自動セットアップ（推奨）
class TodoStore {
  todos = []

  constructor() {
    makeAutoObservable(this)  // すべてを自動で設定
  }

  addTodo(title) {
    this.todos.push({ id: Date.now(), title, completed: false })
  }

  get completedCount() {
    return this.todos.filter(t => t.completed).length
  }
}

// BAD: 普通のJSオブジェクト（MobXは変更を追跡できない）
class PlainStore {
  todos = []  // これは単なる配列、Reactiveではない

  addTodo(title) {
    this.todos.push({ title })  // 変更が検知されない
  }
}
```

**原則**: 変更を追跡したいすべての状態は `observable` にする。ただし、すべてをobservableにする必要はない（React IDやタイマーIDなど）。

### 3. Computed による導出

既存の状態から計算で導出できる値。メモ化されており、依存する状態が変わった時だけ再計算される。

```tsx
class ShoppingCart {
  @observable items = []

  // GOOD: computedで導出（自動メモ化）
  @computed get total() {
    console.log("計算実行")
    return this.items.reduce((sum, item) => sum + item.price, 0)
  }
}

const cart = new ShoppingCart()
cart.items.push({ price: 100 })

// 同じ値に複数回アクセスしても、計算は1回だけ
console.log(cart.total)  // ログ: "計算実行", 100
console.log(cart.total)  // ログなし（キャッシュ）, 100

// 依存する状態が変わると再計算
cart.items.push({ price: 50 })
console.log(cart.total)  // ログ: "計算実行", 150
```

```tsx
// BAD: 通常のメソッド（毎回計算）
get total() {
  console.log("計算実行")
  return this.items.reduce((sum, item) => sum + item.price, 0)
}
// アクセスするたびに計算が走る（非効率）
```

**なぜ重要か**:
- Reactの `useMemo` のようだが、**自動で依存追跡**される
- 無駄な再計算を防ぎ、パフォーマンスを最適化
- 観測されていない時は休止状態（Lazy Evaluation）

### 4. Action による状態変更

状態を変更する操作は必ず `action` でラップする。これによりMobXは変更を一括処理（バッチング）できる。

```tsx
class UserStore {
  @observable firstName = ""
  @observable lastName = ""

  // GOOD: actionで複数の状態変更をバッチング
  @action updateName(first, last) {
    this.firstName = first
    this.lastName = last
    // この2つの変更は1回のリアクションとして処理される
  }
}

// BAD: action外での変更（複数回のリアクションが発生）
store.firstName = "John"  // → 再レンダリング1回目
store.lastName = "Doe"    // → 再レンダリング2回目
// 不要な中間状態が観測され、パフォーマンス低下
```

**厳格モードを有効化（強く推奨）**:
```tsx
import { configure } from "mobx"

configure({
  enforceActions: "always"  // action外での変更を禁止
})
```

**なぜ重要か**:
- **バッチング**: 複数の変更を1回の再レンダリングにまとめる
- **一貫性**: 中間状態（glitch）を防ぐ
- **トレーサビリティ**: DevToolsでアクションの履歴を追跡できる

### 5. Reactivity は自動追跡

MobXは使用されたobservableを自動で追跡し、変更時に再実行する。

```tsx
import { observer } from "mobx-react-lite"

// GOOD: observerでラップ → 使用したobservableを自動追跡
const UserProfile = observer(({ user }) => {
  // user.nameが変わると、このコンポーネントだけが再レンダリング
  return <div>{user.name}</div>
})

// BAD: observerなし → 状態が変わっても再レンダリングされない
const BrokenProfile = ({ user }) => {
  return <div>{user.name}</div>  // 初期値のまま固定される
}
```

**自動追跡の仕組み**:
```tsx
const giraffe = new Animal("Gary")

autorun(() => {
  // この関数内でアクセスしたobservableを自動追跡
  console.log("Energy:", giraffe.energyLevel)
  if (giraffe.isHungry) {  // isHungryもcomputedで追跡される
    console.log("Hungry!")
  }
})

// energyLevelが変わると、autorunが自動で再実行される
giraffe.reduceEnergy()
```

## アンチパターン

### Action外での状態変更（最も重大）

```tsx
// ❌ BAD: action外での変更
class TodoStore {
  @observable todos = []

  // actionがない
  addTodo(title) {
    this.todos.push({ title })  // 危険
  }
}

// 複数の変更で複数回の再レンダリング
store.todos.push({ title: "A" })  // → 再レンダリング
store.todos.push({ title: "B" })  // → 再レンダリング
store.todos.push({ title: "C" })  // → 再レンダリング

// ✅ GOOD: actionでバッチング
class TodoStore {
  @observable todos = []

  @action addTodos(titles) {
    titles.forEach(title => this.todos.push({ title }))
    // すべての変更が1回の再レンダリングにまとめられる
  }
}
```

**なぜ危険か**:
1. **パフォーマンス低下**: 変更ごとに個別の再レンダリング
2. **中間状態の露出**: `firstName`だけ変わって`lastName`が変わる前の状態が見える
3. **デバッグ困難**: DevToolsで変更の履歴が追跡できない

**解決策**: 厳格モードを有効化
```tsx
configure({ enforceActions: "always" })
```

### observerを忘れる（最も多いミス）

```tsx
// ❌ BAD: observerを忘れる
const TodoList = ({ store }) => {
  // store.todosが変わっても再レンダリングされない
  return <ul>{store.todos.map(t => <li>{t.title}</li>)}</ul>
}

// ✅ GOOD: observerでラップ
const TodoList = observer(({ store }) => {
  // store.todosが変わると自動で再レンダリング
  return <ul>{store.todos.map(t => <li>{t.title}</li>)}</ul>
})
```

### プリミティブ値をpropsで渡す

```tsx
class UserStore {
  @observable user = { name: "John", age: 30 }
}

// ❌ BAD: プリミティブ値を渡すと、リアクティビティが失われる
const UserName = observer(({ name }) => <div>{name}</div>)
<UserName name={store.user.name} />  // nameは文字列なので、変更を追跡できない

// ✅ GOOD: オブジェクトごと渡して、コンポーネント内でアクセス
const UserName = observer(({ user }) => <div>{user.name}</div>)
<UserName user={store.user} />  // user.nameの変更を追跡できる
```

### 過剰なComputed

```tsx
// ❌ BAD: 単純な値にcomputed（オーバーヘッド）
@computed get userName() {
  return this.user.name  // 単なる参照、computedにする意味がない
}

// ❌ BAD: 観測されないcomputedは毎回再計算される
class Store {
  @observable items = []

  @computed get total() {
    return this.items.reduce((sum, i) => sum + i.price, 0)
  }
}

// observerコンポーネント外でアクセス
console.log(store.total)  // 毎回計算される（メモ化されない）
console.log(store.total)  // また計算される

// ✅ GOOD: computedは高コストな計算や複数箇所で使う値に限定
@computed get expensiveCalculation() {
  // 複雑な計算やフィルタリング
  return this.items
    .filter(i => i.active)
    .map(i => ({ ...i, total: i.price * i.quantity }))
    .sort((a, b) => b.total - a.total)
}
```

**computedを使うべきケース**:
- 計算コストが高い（O(n)以上のループ、複雑な変換）
- 複数の`observer`コンポーネントで使われる
- 複数のobservableから導出される

### render内での配列操作

```tsx
// ❌ BAD: render内でfilter/map（毎回新しい配列）
const TodoList = observer(({ store }) => {
  // 毎レンダリングで新しい配列が作られる
  const activeTodos = store.todos.filter(t => !t.completed)
  return <List items={activeTodos} />  // 子が不要に再レンダリング
})

// ✅ GOOD: storeでcomputedを定義
class TodoStore {
  @observable todos = []

  @computed get activeTodos() {
    return this.todos.filter(t => !t.completed)
  }
}

const TodoList = observer(({ store }) => {
  // メモ化された値、todosが変わらなければ同じ配列参照
  return <List items={store.activeTodos} />
})
```

### Reactionの未解放

```tsx
// ❌ BAD: 解放しない（メモリリーク）
useEffect(() => {
  autorun(() => {
    console.log(store.value)
  })
  // 解放関数を返さない
}, [])

// ✅ GOOD: 必ず解放
useEffect(() => {
  const dispose = autorun(() => {
    console.log(store.value)
  })
  return dispose  // クリーンアップで解放
}, [])
```

## シニアエンジニアの判断基準

### MobX vs Redux: 使い分け

| 状況 | MobX | Redux |
|------|------|-------|
| **プロジェクト規模** | 小〜中規模、迅速な開発 | 大規模、長期保守が必要 |
| **チームの背景** | OOP経験者が多い | 関数型プログラミング志向 |
| **状態の性質** | 頻繁に変わる複雑な状態（フォーム、リアルタイム） | 明確な状態遷移、厳格なフロー |
| **ボイラープレート** | 最小限（`makeAutoObservable`で完結） | 多い（Redux Toolkitで改善） |
| **デバッグ** | 暗黙的、追跡がやや難しい | 明示的、タイムトラベルデバッグ |
| **学習曲線** | 低い（直感的） | 高い（reducer、middleware） |

### MobX vs MobX-State-Tree

| | MobX | MobX-State-Tree (MST) |
|---|------|----------------------|
| **役割** | 柔軟なリアクティブライブラリ（ゲームエンジン） | 構造化されたフレームワーク（完成品のゲーム） |
| **構造** | 自由（plain objectsやclass） | 厳格（型付きモデルツリー） |
| **状態** | ミュータブル | ミュータブル+イミュータブルスナップショット |
| **機能** | `observable`, `action`, `computed` のみ | スナップショット、パッチ、ランタイム型チェック |
| **選択基準** | 柔軟性重視、既存コードへの導入 | 構造の保証、型安全性、タイムトラベル |

### 状態の粒度設計

```tsx
// ❌ BAD: すべてをobservableに
class Store {
  @observable requestId = ""  // 変わらない識別子
  @observable timerId = null  // React管理すべき
  @observable name = ""       // OK
}

// ✅ GOOD: 変更を追跡すべきものだけobservable
class Store {
  requestId = ""  // 普通のプロパティ
  timerId = null  // 普通のプロパティ
  @observable name = ""  // observableが必要

  constructor() {
    makeAutoObservable(this, {
      requestId: false,  // 除外
      timerId: false     // 除外
    })
  }
}
```

### Store の組織化

```tsx
// ❌ BAD: 単一の巨大Store
class AppStore {
  @observable users = []
  @observable products = []
  @observable orders = []
  @observable ui = {}
  // すべてが1つのStoreに...
}

// ✅ GOOD: ドメインごとにStore分割
class RootStore {
  userStore = new UserStore(this)
  productStore = new ProductStore(this)
  orderStore = new OrderStore(this)
  uiStore = new UIStore(this)

  constructor() {
    makeAutoObservable(this)
  }
}

// 各Storeは独立して管理
class UserStore {
  @observable users = []

  constructor(rootStore) {
    this.rootStore = rootStore
    makeAutoObservable(this)
  }
}
```

## 参考資料

- [MobX Documentation](https://mobx.js.org/)
- [MobX React Integration](https://mobx.js.org/react-integration.html)
- [Understanding Reactivity](https://mobx.js.org/understanding-reactivity.html)
- [MobX vs Redux Comparison](https://blog.logrocket.com/best-practices-mobx-2024/)
- [MobX-State-Tree](https://mobx-state-tree.js.org/)
- [MobX Best Practices 2024](https://bitsrc.io/resources/mobx-tutorial-and-best-practices-for-react-apps-in-2022-clb0k20l5000909l93f9z6n77)
- [Common MobX Pitfalls](https://nigelthorne.com/blog/common-mobx-pitfalls/)
