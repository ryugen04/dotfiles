---
name: graphql-philosophy
description: Use when writing or reviewing GraphQL schemas and queries. Provides core principles (client-driven fetching, thinking in graphs, N+1/DataLoader), anti-patterns (deep nesting, missing pagination), and senior engineer guidelines.
---

# GraphQL Philosophy

GraphQL の設計思想とシニアエンジニアが守るべき原則。

## 核心思想

### 1. クライアント主導のデータフェッチ

クライアントが必要なデータを正確に指定し、過不足なく取得できる。これがGraphQLの最大の特徴。

```graphql
// クライアントは必要なフィールドだけを要求
query {
  user(id: "123") {
    name
    email
    # avatarUrlは不要なら要求しない
  }
}
```

**なぜ重要か**: RESTでは `/users/123` が固定のレスポンス構造を返すため、オーバーフェッチ（不要なデータも取得）やアンダーフェッチ（追加リクエストが必要）が発生する。GraphQLではクライアントが必要なデータを宣言的に要求するため、ネットワーク効率が向上し、モバイルアプリなどの帯域制約環境で特に有効。

### 2. ビジネスドメインをグラフで表現 (Thinking in Graphs)

データをリソースではなく、ノード（型）とエッジ（関係）のグラフとしてモデル化する。

```graphql
# BAD: RESTの発想をそのまま持ち込む
type Query {
  getUserById(id: ID!): User
  getPostsByUserId(userId: ID!): [Post]
  getCommentsByPostId(postId: ID!): [Comment]
}

# GOOD: グラフとして関係を表現
type Query {
  user(id: ID!): User
}

type User {
  id: ID!
  name: String!
  posts: [Post!]!  # ユーザーから投稿への関係
}

type Post {
  id: ID!
  title: String!
  author: User!      # 投稿から作者への関係
  comments: [Comment!]!
}
```

**なぜ重要か**: GraphQLスキーマは「ビジネスドメインの共通言語」として機能する。データベース構造ではなく、クライアントがデータをどう使うかに基づいて設計することで、直感的で保守性の高いAPIになる。

### 3. 型安全な契約

スキーマは型システムによって厳密に定義され、実行時にバリデーションされる。

```graphql
type User {
  id: ID!          # 非null、必ず値が存在
  name: String!    # 非null
  bio: String      # nullable、値がないかもしれない
  posts: [Post!]!  # 非nullの配列、要素も非null
}
```

**なぜ重要か**: 型定義により、クライアントとサーバー間の契約が明確になる。TypeScript等の型生成ツールと組み合わせることで、フロントエンドからバックエンドまでエンドツーエンドの型安全性が実現できる。

### 4. ビジネスロジック層の分離

リゾルバは薄く保ち、ビジネスロジックは専用の層に配置する。

```javascript
// BAD: リゾルバにビジネスロジックを詰め込む
const resolvers = {
  Query: {
    user: async (_, { id }) => {
      const user = await db.users.findById(id)
      if (!user) throw new Error('User not found')
      // 認可チェック
      if (!context.user || context.user.role !== 'admin') {
        delete user.email  // 管理者以外はemailを隠す
      }
      return user
    }
  }
}

// GOOD: ビジネスロジック層を経由
const resolvers = {
  Query: {
    user: (_, { id }, context) => {
      // リゾルバは薄く、ビジネスロジック層に委譲
      return UserService.findById(id, context.user)
    }
  }
}

// ビジネスロジック層（単一の真実の源）
class UserService {
  static async findById(id, currentUser) {
    const user = await db.users.findById(id)
    if (!user) throw new NotFoundError('User not found')

    // 認可はビジネスロジック層で統一的に管理
    return this.authorize(user, currentUser)
  }
}
```

**なぜ重要か**: リゾルバはGraphQLインターフェースの薄いアダプタに過ぎない。ビジネスロジックを分離することで、REST APIや他のインターフェースとロジックを共有でき、テストも容易になる。

### 5. N+1 問題の回避 (DataLoader)

GraphQLの柔軟性がパフォーマンス問題を引き起こす典型例。必ずDataLoaderで対処する。

```javascript
// BAD: N+1問題が発生
const resolvers = {
  Query: {
    users: () => database.fetchAllUsers(),  // 1回
  },
  User: {
    posts: (user) => {
      // ユーザーの数だけ実行される（N回）
      return database.fetchPostsByUserId(user.id)
    }
  }
}

// 実行されるクエリ:
// SELECT * FROM users;
// SELECT * FROM posts WHERE user_id = 1;
// SELECT * FROM posts WHERE user_id = 2;
// SELECT * FROM posts WHERE user_id = 3;
// ... N回繰り返し

// GOOD: DataLoaderでバッチ処理
const DataLoader = require('dataloader')

const postsBatchFn = async (userIDs) => {
  // IN句で1回のクエリにまとめる
  const posts = await database.fetchPostsByUserIds(userIDs)
  // SELECT * FROM posts WHERE user_id IN (1,2,3,...)

  // DataLoaderは入力と同じ順序で結果を返すことを要求
  return userIDs.map(id => posts.filter(post => post.user_id === id))
}

const postsLoader = new DataLoader(postsBatchFn)

const resolvers = {
  Query: {
    users: () => database.fetchAllUsers(),
  },
  User: {
    posts: (user) => postsLoader.load(user.id)  // バッチ処理に追加
  }
}

// 実行されるクエリ:
// SELECT * FROM users;
// SELECT * FROM posts WHERE user_id IN (1,2,3,...);  // 1回だけ
```

**なぜ重要か**: GraphQLでは親オブジェクトのリストを取得後、各要素に対して子リゾルバが呼ばれる。DataLoaderを使わないと、リストの要素数に比例してデータベースクエリが増え、パフォーマンスが壊滅的に悪化する。

## アンチパターン

### 深すぎるネスト（DoS攻撃のリスク）

循環参照が可能なスキーマでは、意図的に深いクエリを送信してサーバーを停止させられる。

```graphql
# BAD: 深度制限がないスキーマ
query MaliciousQuery {
  user(id: "1") {
    posts {
      author {
        posts {
          author {
            posts {
              # 無限に続けられる
            }
          }
        }
      }
    }
  }
}
```

**対策**:
```javascript
// クエリ深度制限を導入
import { createComplexityLimitRule } from 'graphql-validation-complexity'

const server = new ApolloServer({
  schema,
  validationRules: [
    createComplexityLimitRule(1000, {
      onCost: (cost) => console.log('query cost:', cost),
    }),
  ],
})
```

**なぜ重要か**: 悪意のあるクエリがサーバーリソースを枯渇させ、サービス拒否攻撃につながる。クエリの深度やコストを制限することで、システムを保護する。

### 巨大なクエリ（オーバーフェッチ）

一覧表示なのに詳細データまで取得してしまうAIがやりがちなパターン。

```graphql
# BAD: 商品一覧なのに不要なデータまで要求
query GetProductList {
  products(first: 100) {
    id
    name
    price
    description        # 長文、一覧には不要
    specifications {   # 大量のデータ
      key
      value
    }
    reviews {          # 数百件あるかもしれない
      rating
      comment
      author { name }
    }
  }
}

# GOOD: 必要最小限のフィールドのみ
query GetProductList {
  products(first: 10) {  # ページネーションで制限
    id
    name
    price
    imageUrl
  }
}
```

**対策**:
```graphql
# スキーマ側で最大取得数を強制
type Query {
  products(first: Int = 10, after: String): ProductConnection!
}

# バックエンドで上限を設定
const resolvers = {
  Query: {
    products: (_, { first }) => {
      const limit = Math.min(first || 10, 100)  // 最大100件
      return fetchProducts(limit)
    }
  }
}
```

### RESTの思考をGraphQLに持ち込む

データベーステーブルをそのままGraphQL型にマッピングしてしまうパターン。

```graphql
# BAD: データベース構造をそのまま露出
type user_accounts {  # テーブル名そのまま
  user_id: Int!       # カラム名そのまま
  created_at: String
  updated_at: String
  is_deleted: Boolean
}

type Query {
  getUserAccounts: [user_accounts]
  getOrdersByUserId(user_id: Int!): [orders]
}

# GOOD: ビジネスドメインを表現
type User {
  id: ID!
  name: String!
  email: String!
  createdAt: DateTime!
  orders: [Order!]!  # 関係をグラフで表現
}

type Query {
  user(id: ID!): User
  # クライアントはuser.ordersでたどれるので不要
}
```

**なぜ重要か**: GraphQLスキーマはビジネスドメインの抽象化であり、データベース構造の直接露出ではない。クライアントがどうデータを使うかに基づいて設計すべき。

### ページネーションの欠如

リスト型フィールドに上限がないと、パフォーマンス問題とメモリ枯渇を引き起こす。

```graphql
# BAD: 無制限のリスト
type User {
  posts: [Post!]!  # ユーザーが10万件の投稿を持っていたら？
}

# GOOD: Relay-style Cursor Pagination
type User {
  postsConnection(first: Int, after: String): PostConnection!
}

type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int
}

type PostEdge {
  cursor: String!
  node: Post!
}

type PageInfo {
  hasNextPage: Boolean!
  endCursor: String
}
```

**クエリ例**:
```graphql
query {
  user(id: "123") {
    postsConnection(first: 10) {
      edges {
        node {
          title
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}

# 次のページ取得
query {
  user(id: "123") {
    postsConnection(first: 10, after: "Y3Vyc29yMQ==") {
      edges { node { title } }
      pageInfo { hasNextPage, endCursor }
    }
  }
}
```

## シニアエンジニアの判断基準

### GraphQL vs REST の使い分け

| 観点 | GraphQL を選ぶ | REST を選ぶ |
|------|---------------|------------|
| **データ要件** | 複数リソースの集約が必要<br>ネストした関連データ | 単一リソースのCRUD<br>シンプルなデータ構造 |
| **クライアントの多様性** | Web/iOS/Android等で要求が異なる<br>サードパーティ開発者向け | 単一クライアント<br>内部システム間通信 |
| **リアルタイム性** | Subscriptionで双方向通信が必要 | Webhookやポーリングで十分 |
| **キャッシュ** | クライアント側の複雑なキャッシュ<br>（Apollo Client等） | CDNやHTTPキャッシュで十分 |
| **開発速度** | フロントエンド主導の開発<br>APIバージョニングを避けたい | 素早くプロトタイプを作りたい<br>既存のRESTエコシステム活用 |
| **ファイルアップロード** | 可能だが複雑 | マルチパート/フォームデータで簡単 |

### スキーマ設計のチェックリスト

1. **ビジネスドメインの表現**: データベース構造ではなく、クライアントの使い方に基づいて設計しているか？
2. **命名の一貫性**: チーム内で共通の用語を使っているか？
3. **Nullable設計**: 各フィールドが本当にnullableであるべきか検討したか？
4. **ページネーション**: すべてのリスト型フィールドにページネーションを実装したか？
5. **N+1対策**: DataLoaderを導入したか？
6. **深度制限**: クエリの複雑度制限を実装したか？
7. **認可**: ビジネスロジック層で統一的に認可を処理しているか？

### 段階的な導入戦略

GraphQLは全置き換えではなく、段階的に導入すべき：

1. **Phase 1**: 単一ユースケースからスタート（例: ダッシュボードのデータ集約）
2. **Phase 2**: 既存REST APIをGraphQLでラップ
3. **Phase 3**: 新機能はGraphQLで実装
4. **Phase 4**: レガシーRESTを段階的に移行

## 参考資料

- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [Thinking in Graphs](https://graphql.org/learn/thinking-in-graphs/)
- [GraphQL Security](https://graphql.org/learn/security/)
- [Apollo Server - DataLoader](https://www.apollographql.com/docs/apollo-server/data/data-sources/)
- [Principled GraphQL](https://principledgraphql.com/)
- [GraphQL Pagination](https://graphql.org/learn/pagination/)
