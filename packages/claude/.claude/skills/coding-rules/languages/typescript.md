---
name: typescript-philosophy
description: Use when writing or reviewing TypeScript code. Provides core principles (structural typing, type inference, discriminated unions), anti-patterns (any abuse, type assertion overuse), and senior engineer guidelines.
---

# TypeScript Philosophy

TypeScript の設計思想とシニアエンジニアが守るべき原則。

## 核心思想

### 1. 構造的型付け（Structural Typing）

TypeScriptは「名前」ではなく「形状（shape）」で型を判定する。これは「ダックタイピング」とも呼ばれる。

```typescript
// 明示的な継承関係がなくても、同じ構造なら互換性がある
interface Point {
  x: number
  y: number
}

class Vector {
  constructor(public x: number, public y: number) {}
}

function distance(p: Point) {
  return Math.sqrt(p.x ** 2 + p.y ** 2)
}

// Vectorは明示的にPointを実装していないが、構造が同じなので使える
const v = new Vector(3, 4)
distance(v) // OK: Vector has x and y properties
```

**なぜ重要か**: JavaScriptの柔軟性を保ちながら型安全性を提供する。オブジェクトリテラル、クラス、インターフェースを同じように扱える。

**注意点**: 構造的型付けゆえに、意図しない互換性が生まれることがある。

```typescript
type UserId = string
type ProductId = string

// ❌ BAD: 構造的には同じなので区別できない
function getUser(id: UserId) { /* ... */ }
const productId: ProductId = "prod-123"
getUser(productId) // エラーにならない！

// ✅ GOOD: Branded Typeで区別可能にする
type UserId = string & { readonly brand: unique symbol }
type ProductId = string & { readonly brand: unique symbol }

function createUserId(id: string): UserId {
  return id as UserId
}
function getUser(id: UserId) { /* ... */ }

const productId = "prod-123" as ProductId
getUser(productId) // Error: Type 'ProductId' is not assignable to type 'UserId'
```

### 2. 型推論の活用

TypeScriptの型推論は強力。明示的な型注釈が不要な場所では、推論に任せる。

```typescript
// ❌ BAD: 冗長な型注釈（AIがやりがち）
let name: string = "Alice"
let count: number = 0
let items: string[] = ["a", "b", "c"]

// ✅ GOOD: 型推論に任せる
let name = "Alice"           // string
let count = 0                // number
let items = ["a", "b", "c"]  // string[]

// ✅ GOOD: 明示的な型注釈が有効な場合
// 1. 関数のパラメータ・戻り値（APIの明確化）
export function add(a: number, b: number): number {
  return a + b
}

// 2. 複雑な型を持つ変数
const config: Record<string, { enabled: boolean; value: number }> = {
  feature1: { enabled: true, value: 100 }
}

// 3. 推論が広すぎる場合
const Status = {
  Active: "active",
  Inactive: "inactive"
} as const  // { readonly Active: "active"; readonly Inactive: "inactive" }
// as constなしだと { Active: string; Inactive: string } に推論される
```

**判断基準**:
- **推論に任せる**: 初期化時に型が明確な変数、単純な計算結果
- **明示する**: 関数シグネチャ、公開API、型が広すぎる場合、後で値が変わる変数

### 3. 型で不正な状態を表現不能にする（Make Impossible States Impossible）

型システムを使って、実行時エラーをコンパイル時に防ぐ。

```typescript
// ❌ BAD: 不正な状態の組み合わせが可能
interface Request {
  state: "pending" | "success" | "error"
  data?: string
  error?: Error
}

// この状態は矛盾している（successなのにerrorがある）
const badRequest: Request = {
  state: "success",
  data: "result",
  error: new Error("oops")  // 型システムはこれを防げない
}

// ✅ GOOD: Discriminated Unionで不正な状態を表現不能にする
type Request =
  | { state: "pending" }
  | { state: "success"; data: string }
  | { state: "error"; error: Error }

// これはコンパイルエラーになる
const goodRequest: Request = {
  state: "success",
  data: "result",
  error: new Error("oops")  // Error: Object literal may only specify known properties
}
```

```typescript
// ❌ BAD: オプショナルの組み合わせで矛盾が生まれる
interface User {
  name: string
  email?: string
  emailVerified?: boolean  // emailがないのにemailVerifiedがtrueになりうる
}

// ✅ GOOD: 状態を明示的に分離
type User =
  | { name: string; email: null }
  | { name: string; email: string; emailVerified: boolean }
```

**原則**: 型定義を見ただけで、取りうる状態の組み合わせが明確に分かるようにする。

### 4. Discriminated Union（判別可能なユニオン型）

共通のリテラル型プロパティ（判別子）を持つ型の組み合わせで、型安全な分岐を実現。

```typescript
// ✅ GOOD: 判別子（kind）で型を安全に絞り込める
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "square"; sideLength: number }
  | { kind: "triangle"; base: number; height: number }

function getArea(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      // この中では shape は { kind: "circle"; radius: number } に絞り込まれる
      return Math.PI * shape.radius ** 2
    case "square":
      return shape.sideLength ** 2
    case "triangle":
      return (shape.base * shape.height) / 2
    default:
      // 全てのケースを網羅していることを保証（Exhaustiveness Checking）
      const _exhaustive: never = shape
      return _exhaustive
  }
}
```

```typescript
// API Result の典型的なパターン
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E }

function handleResult<T>(result: Result<T>) {
  if (result.success) {
    // result.data にアクセス可能
    console.log(result.data)
  } else {
    // result.error にアクセス可能
    console.error(result.error)
  }
}
```

**判別子の選択**:
- `kind`, `type`, `status` など一貫した名前を使う
- **必ずリテラル型**を使う（`string` ではダメ）
- `as const` を活用してリテラル型を保証

### 5. unknown > any

型が不明な場合は `any` ではなく `unknown` を使う。

```typescript
// ❌ BAD: any は型チェックを完全に無効化
function processData(data: any) {
  console.log(data.value.nested.property) // コンパイルは通るが実行時エラーの可能性
}

// ✅ GOOD: unknown は使用前に型チェックを強制
function processData(data: unknown) {
  // console.log(data.value) // Error: Object is of type 'unknown'

  // 型ガードで安全に絞り込む
  if (typeof data === "object" && data !== null && "value" in data) {
    const obj = data as { value: unknown }
    console.log(obj.value)
  }
}
```

**any を使ってもいい場面**（最小限に）:
- サードパーティライブラリの型定義が不完全な場合の一時的な回避策
- 段階的な型付け（JavaScriptからの移行時）
- プロトタイプや実験的なコード

**それ以外は常に unknown を検討する。**

## アンチパターン

### any の乱用

AIが生成したコードの最大の問題。型推論が難しいとすぐ `any` を使う。

```typescript
// ❌ BAD: AIがやりがちな any の乱用
function fetchData(url: string): Promise<any> {  // 戻り値が any
  return fetch(url).then(res => res.json())
}

const data = await fetchData("/api/user")
console.log(data.naem)  // タイポに気づけない（実行時エラー）

// ✅ GOOD: 適切な型定義
interface User {
  name: string
  email: string
}

function fetchData<T>(url: string): Promise<T> {
  return fetch(url).then(res => res.json())
}

const data = await fetchData<User>("/api/user")
console.log(data.naem)  // Error: Property 'naem' does not exist on type 'User'
```

```typescript
// ❌ BAD: イベントハンドラで any
const handleClick = (e: any) => {
  console.log(e.target.value)
}

// ✅ GOOD: 適切な型
const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
  console.log(e.currentTarget.value)
}
```

### 型アサーション (as) の乱用

型アサーションはコンパイラに「自分は型を理解している」と伝える強力な機能。AIは安易に使いがち。

```typescript
// ❌ BAD: 安易な型アサーション
const data = JSON.parse(jsonString) as User
// JSON.parse の結果が本当に User の形をしているか保証されない

// ✅ GOOD: 型ガード関数でバリデーション
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === "object" &&
    obj !== null &&
    "name" in obj &&
    typeof obj.name === "string" &&
    "email" in obj &&
    typeof obj.email === "string"
  )
}

const parsed = JSON.parse(jsonString)
if (isUser(parsed)) {
  const user = parsed  // 型安全に User として扱える
} else {
  throw new Error("Invalid user data")
}
```

```typescript
// ❌ BAD: as で無理やり型を変える
const input = document.getElementById("input") as HTMLInputElement
// もし input が null だったら？

// ✅ GOOD: null チェックと型ガードを併用
const input = document.getElementById("input")
if (input instanceof HTMLInputElement) {
  console.log(input.value)  // 型安全
}
```

**型アサーションが正当な場合**:
- DOM API（`document.getElementById` の戻り値など）で、要素の型を開発者が確実に知っている
- サードパーティライブラリの型定義が不正確な場合
- TypeScript の型推論が保守的すぎる場合（稀）

### 過剰なジェネリクス

AIは型の柔軟性を求めて、不必要にジェネリクスを使いがち。

```typescript
// ❌ BAD: 不要なジェネリクス
function printName<T extends { name: string }>(obj: T): void {
  console.log(obj.name)
}
// T は一度しか使われていない → ジェネリクスは不要

// ✅ GOOD: シンプルに
function printName(obj: { name: string }): void {
  console.log(obj.name)
}
```

```typescript
// ❌ BAD: 過剰に複雑なジェネリクス
function filter<T, Func extends (arg: T) => boolean>(
  arr: T[],
  func: Func
): T[] {
  return arr.filter(func)
}

// ✅ GOOD: 必要最小限
function filter<T>(arr: T[], func: (arg: T) => boolean): T[] {
  return arr.filter(func)
}
```

**ジェネリクスの判断基準**:
1. **型パラメータは2回以上使われているか**（戻り値の推論を含む）
2. **型パラメータが複数の値を関連付けているか**
3. **再利用性が向上するか**

これらを満たさないなら、ジェネリクスは不要。

### Enum の不適切な使用

TypeScript の `enum` は特殊な挙動があり、予期しない問題を引き起こす。

```typescript
// ❌ BAD: enum は実行時に残るコードを生成し、逆引きマップを作る
enum Direction {
  Up,
  Down,
  Left,
  Right
}

// これは以下のようにコンパイルされる（冗長）
var Direction;
(function (Direction) {
    Direction[Direction["Up"] = 0] = "Up";
    Direction[Direction["Down"] = 1] = "Down";
    Direction[Direction["Left"] = 2] = "Left";
    Direction[Direction["Right"] = 3] = "Right";
})(Direction || (Direction = {}));

// ✅ GOOD: Union型とas constを使う（実行時コード不要）
const Direction = {
  Up: "UP",
  Down: "DOWN",
  Left: "LEFT",
  Right: "RIGHT"
} as const

type Direction = typeof Direction[keyof typeof Direction]
// type Direction = "UP" | "DOWN" | "LEFT" | "RIGHT"
```

**例外**: `const enum` は実行時コードを生成しないが、型情報が失われるため使用は慎重に。

### 型推論を無視した冗長な注釈

```typescript
// ❌ BAD: 推論可能な場所で冗長な型注釈
const numbers: number[] = [1, 2, 3]
const result: number = numbers.reduce((a: number, b: number): number => a + b, 0)

// ✅ GOOD: 型推論に任せる
const numbers = [1, 2, 3]
const result = numbers.reduce((a, b) => a + b, 0)
```

## シニアエンジニアの判断基準

### 型定義の選択

| ケース | 推奨 | 理由 |
|--------|------|------|
| オブジェクトの形状定義 | `interface` | 拡張可能、マージ可能、クラスと親和性が高い |
| Union/Intersection型 | `type` | `interface` ではサポートされない |
| Tuple型 | `type` | `type Point = [number, number]` |
| プリミティブのエイリアス | `type` | `type ID = string` |
| 関数型 | `type` または `interface` | どちらでも可（プロジェクトで統一） |
| ライブラリ公開API | `interface` | Declaration Merging が可能 |

### unknown vs any の判断

| 状況 | 推奨 |
|------|------|
| 外部入力（API、ユーザー入力） | `unknown` |
| JSON.parse の結果 | `unknown` |
| サードパーティライブラリの型不備 | `any`（一時的） |
| 段階的な型付け | `any`（移行中のみ） |
| 完全に動的な値 | `unknown` |

### ジェネリクス vs 具象型

```typescript
// ジェネリクスが有効
function first<T>(arr: T[]): T | undefined {
  return arr[0]  // T を2回使用、型の関連性がある
}

// ジェネリクス不要
function logLength<T extends { length: number }>(obj: T): void {
  console.log(obj.length)  // T は1回しか使われない
}
// これで十分
function logLength(obj: { length: number }): void {
  console.log(obj.length)
}
```

### Type Guard の設計

```typescript
// ✅ GOOD: 再利用可能な型ガード
function isString(value: unknown): value is string {
  return typeof value === "string"
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

// ✅ GOOD: カスタム型ガード
interface User {
  name: string
  email: string
}

function isUser(obj: unknown): obj is User {
  return (
    isObject(obj) &&
    "name" in obj &&
    isString(obj.name) &&
    "email" in obj &&
    isString(obj.email)
  )
}
```

### Exhaustiveness Checking の実装

```typescript
type Action =
  | { type: "add"; payload: string }
  | { type: "remove"; payload: number }
  | { type: "clear" }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "add":
      return { ...state, items: [...state.items, action.payload] }
    case "remove":
      return { ...state, items: state.items.filter((_, i) => i !== action.payload) }
    case "clear":
      return { ...state, items: [] }
    default:
      // 新しい action が追加されたら、ここでコンパイルエラーになる
      const _exhaustive: never = action
      return _exhaustive
  }
}
```

## TypeScript 設定のベストプラクティス

### tsconfig.json の推奨設定

```json
{
  "compilerOptions": {
    // 厳格な型チェック（必須）
    "strict": true,                      // 全ての厳格チェックを有効化
    "noImplicitAny": true,              // 暗黙の any を禁止
    "strictNullChecks": true,           // null/undefined の厳格チェック
    "strictFunctionTypes": true,        // 関数型の厳格チェック
    "strictBindCallApply": true,        // bind/call/apply の厳格チェック
    "noImplicitThis": true,             // 暗黙の this を禁止

    // 追加の型チェック（推奨）
    "noUnusedLocals": true,             // 未使用のローカル変数を検出
    "noUnusedParameters": true,         // 未使用のパラメータを検出
    "noImplicitReturns": true,          // 全てのパスで return を強制
    "noFallthroughCasesInSwitch": true, // switch の fallthrough を検出

    // モジュール解決
    "moduleResolution": "bundler",      // 最新の解決方式
    "resolveJsonModule": true,          // JSON インポートを許可
    "esModuleInterop": true,            // CommonJS との相互運用性

    // その他
    "skipLibCheck": true,               // .d.ts のチェックをスキップ（ビルド高速化）
    "forceConsistentCasingInFileNames": true  // ファイル名の大文字小文字を厳格に
  }
}
```

## 参考資料

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/) - 公式ドキュメント
- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/) - 詳細な解説書
- [Structural Type System](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html) - 構造的型付けの説明
- [Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html) - 型の絞り込み
- [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html) - ジェネリクスのベストプラクティス
- [TypeScript ESLint](https://typescript-eslint.io/) - TypeScript用のLintルール
