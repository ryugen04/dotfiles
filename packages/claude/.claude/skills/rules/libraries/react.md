# React Philosophy

React の設計思想とシニアエンジニアが守るべき原則。

## 核心思想

### 1. 宣言的UI
「どうやって」ではなく「何を」描画するかを記述する。

```tsx
// BAD: 命令的（DOM操作で直接更新）
document.getElementById('list').textContent = ''
items.forEach(i => {
  const li = document.createElement('li')
  li.textContent = i.name
  document.getElementById('list').appendChild(li)
})

// GOOD: 宣言的（状態から導出）
return <ul>{items.map(i => <li key={i.id}>{i.name}</li>)}</ul>
```

### 2. 単方向データフロー
状態は上から下へ流れる。子から親への通信はコールバック経由。

```tsx
// BAD: 双方向バインディング的な発想
<Input value={value} onChange={e => parent.value = e.target.value} />

// GOOD: 明示的なコールバック
<Input value={value} onChange={onValueChange} />
```

### 3. コンポジション（継承より合成）
コンポーネントは継承ではなく、合成で拡張する。

```tsx
// BAD: 継承
class PrimaryButton extends Button { ... }

// GOOD: 合成
const PrimaryButton = (props) => <Button variant="primary" {...props} />
```

### 4. 最小限の状態
本当に必要な状態だけを持つ。導出可能な値は状態にしない。

```tsx
// BAD: 導出値を状態に持つ
const [firstName, setFirstName] = useState('')
const [lastName, setLastName] = useState('')
const [fullName, setFullName] = useState('')  // 導出可能

// GOOD: 計算で導出
const fullName = `${firstName} ${lastName}`
```

## アンチパターン

### useEffect の乱用

```tsx
// BAD: 状態同期に useEffect
const [firstName, setFirstName] = useState('')
const [lastName, setLastName] = useState('')
const [fullName, setFullName] = useState('')

useEffect(() => {
  setFullName(`${firstName} ${lastName}`)
}, [firstName, lastName])

// GOOD: 導出状態は計算で
const fullName = `${firstName} ${lastName}`
```

```tsx
// BAD: 初期化に useEffect
useEffect(() => {
  fetchUser().then(setUser)
}, [])

// GOOD: Suspense + use() または React Query/SWR
const user = use(fetchUser())
```

### 不要な useMemo/useCallback

```tsx
// BAD: AI がやりがちな過剰最適化
const formattedDate = useMemo(() =>
  new Date(date).toLocaleDateString(), [date]
)
const handleClick = useCallback(() => {
  setCount(c => c + 1)
}, [])

// GOOD: 単純な計算は直接（子が memo 化されていなければ useCallback も不要）
const formattedDate = new Date(date).toLocaleDateString()
const handleClick = () => setCount(c => c + 1)
```

**useMemo/useCallback が有効な場合:**
- 計算コストが高い（O(n)以上のループ、複雑な変換）
- 参照等価性が重要（memo化された子コンポーネントへのprops）
- カスタムフックの戻り値の安定化

### 過剰な状態分割

```tsx
// BAD: 関連する状態が分散
const [firstName, setFirstName] = useState('')
const [lastName, setLastName] = useState('')
const [email, setEmail] = useState('')
const [phone, setPhone] = useState('')

// GOOD: 関連する状態はまとめる
const [form, setForm] = useState({
  firstName: '',
  lastName: '',
  email: '',
  phone: ''
})
```

### Props バケツリレー（Prop Drilling）

```tsx
// BAD: 深いprops転送
<App user={user}>
  <Layout user={user}>
    <Sidebar user={user}>
      <UserMenu user={user} />
    </Sidebar>
  </Layout>
</App>

// GOOD: Context または コンポジション
// Context パターン
const UserContext = createContext(null)
<UserContext.Provider value={user}>
  <App />
</UserContext.Provider>

// コンポジションパターン（より推奨）
<App>
  <Layout sidebar={<Sidebar><UserMenu user={user} /></Sidebar>}>
    {children}
  </Layout>
</App>
```

### キーの誤用

```tsx
// BAD: インデックスをキーに使う（並び替え・削除がある場合）
items.map((item, index) => <Item key={index} {...item} />)

// BAD: ランダムなキー（毎レンダリングで変わる）
items.map(item => <Item key={Math.random()} {...item} />)

// GOOD: 安定した一意の識別子
items.map(item => <Item key={item.id} {...item} />)
```

## シニアエンジニアの判断基準

### 状態管理の選択

| 状態の種類 | 推奨 |
|-----------|------|
| UIローカル状態 | useState |
| 複雑なローカル状態 | useReducer |
| ツリー全体で共有 | Context + useReducer |
| サーバー状態 | React Query / SWR |
| URLと同期 | URL パラメータ |
| グローバル複雑 | Zustand / Jotai |

### コンポーネント分割の指針

1. **単一責任**: 1つのコンポーネントは1つのことをする
2. **再利用性**: 3回以上使うなら抽出を検討
3. **テスト容易性**: テストしやすい単位で分割
4. **可読性**: 100行を超えたら分割を検討

### レンダリング最適化の順序

1. まず正しく動かす
2. パフォーマンス問題が発生したら計測
3. ボトルネックを特定してから最適化
4. memo, useMemo, useCallback は最後の手段

## 参考資料

- [React 公式ドキュメント - Thinking in React](https://react.dev/learn/thinking-in-react)
- [React 公式ドキュメント - You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
