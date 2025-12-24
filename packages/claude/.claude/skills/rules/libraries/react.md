# React Philosophy

React の設計思想とシニアエンジニアが守るべき原則。

## 核心思想

### 1. UI = f(state)

UIは状態の関数である。開発者は状態を管理し、Reactがその状態に基づいてUIを効率的に更新する。

```tsx
// この思想を理解すると、UIの一貫性が保たれる
// 状態が同じなら、UIも同じになる
function Counter({ count }: { count: number }) {
  // countという状態から、UIが決定論的に導出される
  return <span>{count}</span>
}
```

### 2. 宣言的UI

「どうやって（How）」ではなく「何を（What）」描画するかを記述する。

```tsx
// BAD: 命令的（DOM操作で直接更新）
document.getElementById('list').textContent = ''
items.forEach(i => {
  const li = document.createElement('li')
  li.textContent = i.name
  document.getElementById('list').appendChild(li)
})

// GOOD: 宣言的（状態から導出）
// 「このような見た目であるべき」を宣言するだけ
return <ul>{items.map(i => <li key={i.id}>{i.name}</li>)}</ul>
```

**なぜ重要か**: 開発者はDOMを直接操作する必要がなく、状態管理に集中できる。コードはより予測可能になり、バグが発生しにくくなる。

### 3. 単方向データフロー

データは親から子へ一方向に流れる。子から親への通信はコールバック経由。

```tsx
// BAD: 子が親の状態を直接変更しようとする発想
<Input value={value} onChange={e => parent.value = e.target.value} />

// GOOD: 親から渡されたコールバックを呼び出す
<Input value={value} onChange={onValueChange} />
```

**なぜ重要か**:
- **予測可能性**: データの変更元を追跡しやすい
- **デバッグ容易**: どこで何が変わったか明確
- **カプセル化**: Stateは特定のコンポーネントにローカル

### 4. コンポジション（継承より合成）

コンポーネントは継承ではなく、合成で拡張する。

```tsx
// BAD: 継承（Reactでは推奨されない）
class PrimaryButton extends Button { ... }

// GOOD: 合成（propsで振る舞いを変える）
const PrimaryButton = (props) => <Button variant="primary" {...props} />

// BETTER: childrenを活用した柔軟なコンポジション
function Card({ children }: { children: React.ReactNode }) {
  return <div className="card">{children}</div>
}

// 親が中身を自由に決められる
<Card>
  <UserAvatar />
  <UserBio />
</Card>
```

**React公式の見解**: 「コンポーネントの継承階層を作成することが推奨されるユースケースは見つかっていない」

### 5. 最小限の状態

本当に必要な状態だけを持つ。導出可能な値は状態にしない。

```tsx
// BAD: 導出可能な値を状態に持つ（冗長）
const [firstName, setFirstName] = useState('')
const [lastName, setLastName] = useState('')
const [fullName, setFullName] = useState('')  // firstName + lastName で導出可能

useEffect(() => {
  setFullName(`${firstName} ${lastName}`)  // 不要な同期
}, [firstName, lastName])

// GOOD: レンダリング中に計算で導出
const [firstName, setFirstName] = useState('')
const [lastName, setLastName] = useState('')
const fullName = `${firstName} ${lastName}`  // 状態ではなく計算値
```

**原則**: 既存のpropsやstateから計算できる値は、stateに保存せずレンダリング中に計算する。

## アンチパターン

### useEffect の乱用

useEffectは「外部システムとの同期」のためのエスケープハッチ。それ以外の用途は大抵誤用。

```tsx
// ❌ BAD: 状態同期に useEffect（最も多いAIの誤用）
useEffect(() => {
  setFullName(`${firstName} ${lastName}`)
}, [firstName, lastName])

// ✅ GOOD: 導出状態は計算で
const fullName = `${firstName} ${lastName}`
```

```tsx
// ❌ BAD: データ変換に useEffect
useEffect(() => {
  setVisibleTodos(todos.filter(t => t.visible))
}, [todos])

// ✅ GOOD: レンダリング中に計算
const visibleTodos = todos.filter(t => t.visible)
```

```tsx
// ❌ BAD: ユーザーイベントの処理に useEffect
useEffect(() => {
  if (submitted) {
    sendFormData(formData)
  }
}, [submitted])

// ✅ GOOD: イベントハンドラで直接処理
const handleSubmit = () => {
  sendFormData(formData)
}
```

**useEffectが正当な場合**:
- DOMの直接操作（フォーカス、スクロール位置）
- 外部サービスとの接続（WebSocket、サードパーティAPI）
- タイマー・インターバルの設定
- ブラウザAPIとの同期（ウィンドウサイズ、イベントリスナー）

### useMemo/useCallback の過剰使用（AIがやりがち）

**React公式の見解**: 「useMemoはパフォーマンス最適化としてのみ使用すべき。これがないとコードが動かない場合、まず根本的な問題を見つけて修正すべき」

```tsx
// ❌ BAD: 単純な計算にuseMemo（AIがやりがち）
const formattedDate = useMemo(() =>
  new Date(date).toLocaleDateString(), [date]
)

// ✅ GOOD: 単純な計算は直接
const formattedDate = new Date(date).toLocaleDateString()
```

```tsx
// ❌ BAD: memo化されていないコンポーネントへの関数渡しにuseCallback
const handleClick = useCallback(() => {
  setCount(c => c + 1)
}, [])
return <Button onClick={handleClick} />  // Buttonがmemo化されていなければ意味なし

// ✅ GOOD: 子がmemo化されていなければuseCallbackは不要
const handleClick = () => setCount(c => c + 1)
return <Button onClick={handleClick} />
```

**useMemo/useCallbackが有効な場合**:
- 計算コストが高い（O(n)以上のループ、複雑な変換）
- `React.memo`でラップされた子コンポーネントへのprops
- 他のフックの依存配列に含まれる値/関数の安定化
- カスタムフックの戻り値の安定化

**メモ化の前に検討すべきこと（Dan Abramov "Before You memo()"より）**:
1. **状態の移動**: 状態をツリーの葉に近いコンポーネントに移動
2. **コンテンツのリフトアップ**: `children`を活用して静的な部分を分離

```tsx
// メモ化よりこのパターンを優先
function PageLayout({ children }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  // isMenuOpenが変わっても、childrenは再レンダリングされない
  return (
    <div>
      <nav>{/* ... */}</nav>
      {children}
    </div>
  )
}
```

### 過剰な状態分割

```tsx
// ❌ BAD: 関連する状態が分散
const [firstName, setFirstName] = useState('')
const [lastName, setLastName] = useState('')
const [email, setEmail] = useState('')
const [phone, setPhone] = useState('')

// ✅ GOOD: 関連する状態はまとめる
const [form, setForm] = useState({
  firstName: '',
  lastName: '',
  email: '',
  phone: ''
})
```

### Props バケツリレー（Prop Drilling）

```tsx
// ❌ BAD: 深いprops転送
<App user={user}>
  <Layout user={user}>
    <Sidebar user={user}>
      <UserMenu user={user} />
    </Sidebar>
  </Layout>
</App>

// ✅ GOOD: コンポジションパターン（より推奨）
<App>
  <Layout sidebar={<Sidebar><UserMenu user={user} /></Sidebar>}>
    {children}
  </Layout>
</App>

// ✅ GOOD: Context（グローバルに必要な場合）
const UserContext = createContext(null)
<UserContext.Provider value={user}>
  <App />
</UserContext.Provider>
```

### キーの誤用

```tsx
// ❌ BAD: インデックスをキーに使う（並び替え・削除がある場合）
items.map((item, index) => <Item key={index} {...item} />)

// ❌ BAD: ランダムなキー（毎レンダリングで変わる）
items.map(item => <Item key={Math.random()} {...item} />)

// ✅ GOOD: 安定した一意の識別子
items.map(item => <Item key={item.id} {...item} />)
```

**keyの役割**: Reactが要素の同一性を追跡するための識別子。不安定なkeyは不要な再マウントを引き起こす。

## シニアエンジニアの判断基準

### 状態管理の選択

| 状態の種類 | 推奨 | 理由 |
|-----------|------|------|
| UIローカル状態 | useState | シンプル、コンポーネントに閉じる |
| 複雑なローカル状態 | useReducer | 状態遷移ロジックを一箇所に集約 |
| ツリー全体で共有 | Context + useReducer | グローバルな状態を明示的に管理 |
| サーバー状態 | React Query / SWR | キャッシュ、再検証、楽観的更新 |
| URLと同期 | URL パラメータ | ブックマーク可能、共有可能 |
| グローバル複雑 | Zustand / Jotai | 軽量、ボイラープレート少 |

### コンポーネント分割の指針

1. **単一責任**: 1つのコンポーネントは1つのことをする
2. **再利用性**: 3回以上使うなら抽出を検討
3. **テスト容易性**: テストしやすい単位で分割
4. **可読性**: 100行を超えたら分割を検討

### レンダリング最適化の順序

1. **まず正しく動かす** - 最適化は後
2. **パフォーマンス問題が発生したら計測** - React DevTools Profiler
3. **ボトルネックを特定してから最適化** - 推測で最適化しない
4. **memo, useMemo, useCallback は最後の手段** - アーキテクチャ改善を先に検討

## React 18/19 の新パラダイム

### Server Components

デフォルトでサーバー実行。クライアントで実行が必要な場合のみ`'use client'`を付ける。

```tsx
// Server Component（デフォルト）
// - サーバーでのみ実行
// - useState, useEffectは使えない
// - データベースに直接アクセス可能
async function UserProfile({ userId }) {
  const user = await db.user.findById(userId)  // サーバーで実行
  return <div>{user.name}</div>
}

// Client Component
'use client'
// - クライアントで実行
// - インタラクティビティが必要な場合
function LikeButton() {
  const [liked, setLiked] = useState(false)
  return <button onClick={() => setLiked(!liked)}>Like</button>
}
```

**判断基準**:
- インタラクティビティ（useState, イベントハンドラ）→ Client
- ブラウザAPI（localStorage, window）→ Client
- データフェッチ、静的表示 → Server

### Concurrent Features

```tsx
// useTransition: 緊急でない更新をマーク
const [isPending, startTransition] = useTransition()

const handleSearch = (query) => {
  startTransition(() => {
    setSearchResults(filterLargeList(query))  // 緊急でない
  })
}

// useDeferredValue: 値の更新を遅延
const deferredQuery = useDeferredValue(query)
// 緊急の更新が終わった後にレンダリング
```

### React Compiler

将来的に手動のuseMemo/useCallbackは不要になる。Compilerが自動でメモ化を適用。

```tsx
// 将来はこれだけで十分
function Component({ items }) {
  // Compilerが必要に応じて自動メモ化
  const filtered = items.filter(i => i.active)
  const handleClick = () => console.log('clicked')

  return <List items={filtered} onClick={handleClick} />
}
```

## 参考資料

- [Thinking in React](https://react.dev/learn/thinking-in-react)
- [You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
- [A Complete Guide to useEffect](https://overreacted.io/a-complete-guide-to-useeffect/) - Dan Abramov
- [Before You memo()](https://overreacted.io/before-you-memo/) - Dan Abramov
- [When to useMemo and useCallback](https://kentcdodds.com/blog/usememo-and-usecallback) - Kent C. Dodds
- [React Server Components](https://react.dev/learn/react-server-components)
