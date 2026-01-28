---
name: apollo-client-philosophy
description: Use when writing or reviewing Apollo Client code. Provides core principles (normalized cache, declarative data fetching, fetch policies), anti-patterns (refetchQueries overuse, wrong fetch policy), and senior engineer guidelines.
---

# Apollo Client Philosophy

Apollo Client の設計思想とシニアエンジニアが守るべき原則。

## 核心思想

### 1. 正規化キャッシュ（Normalized Cache）

GraphQLのレスポンスをツリー構造のまま保存するのではなく、各オブジェクトを個別に分解してフラットなテーブル構造で管理する。

```tsx
// ❌ BAD: キャッシュの正規化を活用できていない
import { useMutation, useQuery } from '@apollo/client';
import { UPDATE_USER_AVATAR, GET_POSTS_BY_USER } from './graphql';

function UserProfile({ userId }) {
  const { data } = useQuery(GET_POSTS_BY_USER, { variables: { userId } });
  const [updateUserAvatar] = useMutation(UPDATE_USER_AVATAR, {
    // 投稿リストを再取得しており、非効率
    refetchQueries: [{ query: GET_POSTS_BY_USER, variables: { userId } }],
  });

  const handleAvatarUpdate = (newAvatarUrl) => {
    updateUserAvatar({ variables: { userId, avatarUrl: newAvatarUrl } });
  };
  // ...
}
```

```tsx
// ✅ GOOD: 正規化キャッシュによる自動更新
// ミューテーションが更新後のUserオブジェクトを返すように設計
import { useMutation, useQuery } from '@apollo/client';
import { UPDATE_USER_AVATAR, GET_POSTS_BY_USER } from './graphql';

// UPDATE_USER_AVATAR が id, __typename, avatarUrl を返す
/*
mutation UpdateUserAvatar($userId: ID!, $avatarUrl: String!) {
  updateUser(id: $userId, avatarUrl: $avatarUrl) {
    id
    __typename
    avatarUrl
  }
}
*/

function UserProfile({ userId }) {
  const { data } = useQuery(GET_POSTS_BY_USER, { variables: { userId } });
  // refetchQueriesは不要 - キャッシュが自動で更新される
  const [updateUserAvatar] = useMutation(UPDATE_USER_AVATAR);

  const handleAvatarUpdate = (newAvatarUrl) => {
    updateUserAvatar({ variables: { userId, avatarUrl: newAvatarUrl } });
  };
  // ...
}
```

**なぜ重要か**: 同じデータが複数のクエリで取得されてもキャッシュ内では一元管理される。あるミューテーションがオブジェクトを更新すると、そのオブジェクトを参照している全てのUIが自動的に更新される。不要なrefetchが減り、パフォーマンスが大幅に向上する。

### 2. 宣言的データ取得

「どうやって（How）」ではなく「どの（What）」データが必要かを記述する。

```tsx
// ❌ BAD: 命令的なデータ取得 (useEffect + useState)
import { useState, useEffect } from 'react';
import { client } from './apollo-client';
import { GET_TODOS } from './graphql';

function TodoList() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    client.query({ query: GET_TODOS })
      .then(result => {
        setTodos(result.data.todos);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;
  // ... render todos
}
```

```tsx
// ✅ GOOD: 宣言的なデータ取得 (useQuery)
import { useQuery } from '@apollo/client';
import { GET_TODOS } from './graphql';

function TodoList() {
  const { data, loading, error } = useQuery(GET_TODOS);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;
  // ... render data.todos
}
```

**なぜ重要か**: コンポーネントの関心を「UIの表示」に集中できる。データ取得に関するボイラープレート（ローディング・エラー状態管理）を大幅に削減し、コードの可読性と保守性が向上する。

### 3. キャッシュファーストアーキテクチャ

デフォルトで`cache-first`ポリシーを使用。まずローカルキャッシュを確認し、データがあればネットワークリクエストを行わない。

**Apollo Clientの動作**:
1. データ取得時、まずキャッシュを確認
2. キャッシュにあれば即座に返す（ネットワークリクエストなし）
3. キャッシュになければネットワークリクエストを送信
4. 取得したデータをキャッシュに保存して返す

これにより、アプリケーションの応答性が向上し、不要なネットワーク通信が削減される。

## フェッチポリシーの選択

### 各ポリシーの特性

| ポリシー | 動作 | ユースケース |
|---------|------|-------------|
| `cache-first` (デフォルト) | まずキャッシュ確認、なければネットワーク | 静的/頻繁に更新されないデータ |
| `cache-and-network` | キャッシュを即返却 + 同時にネットワーク取得 | SNSフィード等、即時表示と最新性の両立 |
| `network-only` | 常にネットワーク取得（キャッシュに書き込む） | 常に最新が必要（株価、残高） |
| `cache-only` | キャッシュのみ確認、ネットワークなし | オフライン動作、事前取得済みデータ |
| `no-cache` | 常にネットワーク取得（キャッシュに書き込まない） | 機密情報、一時的な取得 |
| `standby` | 自動実行せず、手動トリガーを待機 | `useLazyQuery`の内部動作 |

### ユースケース別実装

```tsx
// ✅ GOOD: ユースケースに応じた適切なポリシー選択
import { useQuery } from '@apollo/client';
import { GET_LIVE_STOCK_PRICE, GET_USER_PROFILE, GET_NEWS_FEED } from './graphql';

// プロフィール情報: 頻繁に変わらない
function UserProfile({ userId }) {
  const { data } = useQuery(GET_USER_PROFILE, {
    variables: { userId },
    fetchPolicy: 'cache-first', // 適切
  });
  // ...
}

// 株価: 常に最新が必要
function StockTicker({ symbol }) {
  const { data } = useQuery(GET_LIVE_STOCK_PRICE, {
    variables: { symbol },
    fetchPolicy: 'network-only', // 適切
    pollInterval: 5000, // 5秒ごとに最新情報を取得
  });
  // ...
}

// SNSフィード: 即時表示とバックグラウンド更新を両立
function NewsFeed() {
  const { data } = useQuery(GET_NEWS_FEED, {
    fetchPolicy: 'cache-and-network', // 適切
  });
  // ...
}
```

## 楽観的更新（Optimistic Updates）

サーバーレスポンスを待たずにUIを即座に更新する手法。

### 基本パターン

```tsx
import { useMutation } from '@apollo/client';
import { ADD_TODO, GET_TODOS } from './graphql';

function AddTodo() {
  let input;
  const [addTodo] = useMutation(ADD_TODO, {
    // update関数でキャッシュを直接操作
    update(cache, { data: { addTodo } }) {
      const { todos } = cache.readQuery({ query: GET_TODOS });
      cache.writeQuery({
        query: GET_TODOS,
        data: { todos: [...todos, addTodo] },
      });
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.value.trim()) return;

    addTodo({
      variables: { text: input.value },
      optimisticResponse: {
        __typename: 'Mutation',
        addTodo: {
          id: `temp-id-${Date.now()}`, // 仮のID
          __typename: 'Todo',
          completed: false,
          text: input.value,
        },
      },
    });
    input.value = '';
  };

  return (
    <form onSubmit={handleSubmit}>
      <input ref={node => { input = node; }} />
      <button type="submit">Add Todo</button>
    </form>
  );
}
```

**ベストプラクティス**:
- `optimisticResponse`には`__typename`と`id`を必ず含める
- 新規作成時は仮のIDを割り当てる（`temp-id-${Date.now()}`など）

### キャッシュ更新戦略の比較

| 方法 | 長所 | 短所 | 使い所 |
|-----|------|------|--------|
| `refetchQueries` | 実装が簡単 | 常にネットワーク通信、非効率 | 最終手段 |
| 自動正規化 | 最も効率的、コード不要 | リスト操作には使えない | 既存オブジェクトの更新 |
| `cache.modify` | 柔軟、楽観的更新と組み合わせ可 | やや複雑 | **最推奨** リスト操作 |

## アンチパターン

### キャッシュ無視のrefetch多用（AIがやりがち）

```tsx
// ❌ BAD: ミューテーション後に全クエリを再取得
const [addTodo] = useMutation(ADD_TODO, {
  refetchQueries: [
    { query: GET_TODOS }, // 不要なネットワークリクエスト
    { query: GET_USER_STATS },
  ],
});
```

```tsx
// ✅ GOOD: キャッシュを直接更新
const [addTodo] = useMutation(ADD_TODO, {
  update(cache, { data: { addTodo } }) {
    const { todos } = cache.readQuery({ query: GET_TODOS });
    cache.writeQuery({
      query: GET_TODOS,
      data: { todos: [...todos, addTodo] },
    });
  }
});
```

**なぜ問題か**: `refetchQueries`は本来キャッシュのローカル更新で対応できる場面で不要なネットワークリクエストを発生させる。サーバー負荷増大、UI応答性低下、Apollo Clientの正規化キャッシュという利点を完全に無視している。

### 不適切なフェッチポリシー

```tsx
// ❌ BAD: 動的なデータにcache-first
function Notifications() {
  // デフォルトのcache-firstが使われる
  const { data } = useQuery(GET_NOTIFICATIONS);
  // ... 新しい通知が来てもUIが更新されない
}
```

```tsx
// ✅ GOOD: ユースケースに合ったポリシー
function Notifications() {
  const { data } = useQuery(GET_NOTIFICATIONS, {
    fetchPolicy: 'cache-and-network', // まずキャッシュ表示、裏で最新取得
    pollInterval: 60000, // 60秒ごとにチェック
  });
  // ...
}
```

### その他のアンチパターン

- **巨大な単一クエリの作成**: 複数のコンポーネント/ページのデータを1つの巨大なクエリで取得。コンポーネントごとにフラグメントやクエリに分割すべき。
- **クライアントサイドでのフィルタリング/ソート多用**: サーバー側で実行できる処理を、全データ取得後にクライアントで実行。過剰なデータ転送を引き起こす。
- **グローバルエラーハンドリングの欠如**: 各`useQuery`/`useMutation`で個別にエラー処理するだけ。`ApolloLink`で中央集権的なエラーハンドリングを構築すべき。
- **`useLazyQuery`の不適切な使用**: `useEffect`内で`useLazyQuery`を呼び出すなど。`useQuery`の`skip`オプションでシンプルに実現できることが多い。
- **キャッシュIDの不一致**: ミューテーションのレスポンスや`optimisticResponse`の`__typename`/`id`がキャッシュ内オブジェクトと不一致。正規化が機能せず自動更新されない。

## 型安全なクエリ（GraphQL Code Generator）

GraphQLスキーマとクエリを解析し、TypeScript型定義と型付きHooksを自動生成。

### 設定例

```typescript
// codegen.ts
import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  overwrite: true,
  schema: 'http://localhost:4000/graphql',
  documents: 'src/**/*.graphql',
  generates: {
    'src/generated/graphql.tsx': {
      plugins: [
        'typescript',
        'typescript-operations',
        'typescript-react-apollo' // Apollo Client用Hooks生成
      ],
      config: {
        withHooks: true,
      },
    },
  },
};
export default config;
```

### 使用例

```graphql
# src/graphql/queries.graphql
query GetUsers {
  users {
    id
    name
    email
  }
}
```

```tsx
// UserList.tsx
import React from 'react';
import { useGetUsersQuery } from '../generated/graphql';

export const UserList = () => {
  // data, loading, errorはすべて型付けされている
  const { data, loading, error } = useGetUsersQuery();

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <ul>
      {/* data.usersは完全に型付けされており、自動補完が効く */}
      {data?.users.map(user => (
        <li key={user.id}>
          {user.name} ({user.email})
        </li>
      ))}
    </ul>
  );
};
```

**なぜ重要か**:
- **コンパイル時エラー検知**: スキーマとクエリの不整合を実行前に検知
- **優れた開発体験**: 自動補完により開発効率が劇的に向上
- **リファクタリング容易**: スキーマ変更が即座に型定義に反映

## シニアエンジニアの判断基準

### Apollo Client vs React Query

| 項目 | Apollo Client | React Query |
|-----|--------------|-------------|
| 主な用途 | GraphQL専用の包括的状態管理 | REST/GraphQL汎用のサーバー状態管理 |
| 強み | GraphQL深い統合、正規化キャッシュ、サブスクリプション | API非依存、軽量、シンプル設定 |
| 弱み | REST APIサポート限定的、バンドル大 | 正規化キャッシュなし、ローカル状態対象外 |
| 選択基準 | GraphQLが主、正規化が必要、リアルタイム更新 | RESTが主、軽量重視、複数API混在 |

### フェッチポリシーの選択基準

| データ特性 | 推奨ポリシー | 理由 |
|-----------|-------------|------|
| 静的コンテンツ | `cache-first` | 最速応答、ネットワーク節約 |
| ユーザープロフィール | `cache-first` | 頻繁に変わらない |
| SNSフィード | `cache-and-network` | 即時表示と最新性の両立 |
| 通知リスト | `cache-and-network` + polling | バックグラウンド更新 |
| 株価・残高 | `network-only` + polling | 常に最新が必須 |
| 一時的な取得 | `no-cache` | キャッシュ汚染を避ける |

## 参考資料

- [Apollo Client Documentation](https://www.apollographql.com/docs/react/)
- [Demystifying the Apollo Client cache](https://www.apollographql.com/blog/apollo-client/caching/demystifying-the-apollo-client-cache/)
- [Stop using refetchQueries](https://www.apollographql.com/blog/apollo-client/performance/stop-using-refetchqueries/)
- [Apollo Client Fetch Policy: A Deep Dive](https://www.thisdot.co/blog/apollo-client-fetch-policy-a-deep-dive)
- [Apollo Client Antipatterns to Avoid](https://blog.logrocket.com/apollo-client-antipatterns-to-avoid/)
- [GraphQL Code Generator Documentation](https://the-guild.dev/graphql/codegen)
