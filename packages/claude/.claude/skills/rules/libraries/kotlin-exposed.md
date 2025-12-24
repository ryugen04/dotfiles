---
name: kotlin-exposed-philosophy
description: Use when writing or reviewing Kotlin Exposed code. Provides core principles (SQL-first, DSL vs DAO, transaction management), anti-patterns (N+1 queries, operations outside transaction), and senior engineer guidelines.
---

# Kotlin Exposed Philosophy

Kotlin Exposed の設計思想とシニアエンジニアが守るべき原則。

## 核心思想

### 1. SQLファースト、型安全性

Exposedは完全なORMではなく、**軽量なSQL-Builderライブラリ**。データベースを隠蔽するのではなく、型安全にSQLを記述することを目指す。

```kotlin
// SQLクエリとほぼ1対1で対応する型安全なコード
Users.select { Users.active eq true }
    .orderBy(Users.name)
    .map { it[Users.name] }

// 発行されるSQLが容易に予測できる
// SELECT name FROM Users WHERE active = true ORDER BY name
```

**なぜ重要か**:
- コンパイル時に型エラーを検出できる（実行時エラーではない）
- 発行されるSQLを完全に制御できるため、パフォーマンスチューニングが容易
- 「魔法」が少なく、予測可能な動作

### 2. スキーマ定義による型安全性の実現

テーブルとカラムをKotlinのオブジェクトとプロパティとして定義することで、コンパイラがSQL操作を検証する。

```kotlin
object Users : Table() {
    val id = integer("id").autoIncrement()
    val name = varchar("name", 50)
    val age = integer("age")
    override val primaryKey = PrimaryKey(id)
}

transaction {
    // GOOD: 型が一致している
    Users.insert {
        it[name] = "Alice"
        it[age] = 30
    }

    // BAD: integer型にStringを代入 -> コンパイルエラー
    // Users.insert {
    //     it[age] = "not-a-number" // Type mismatch
    // }

    // BAD: 存在しないカラムを参照 -> コンパイルエラー
    // Users.select { Users.nonExistentColumn eq "something" }
}
```

**なぜ重要か**:
- SQLのタイポや型の不一致を実行前に検出
- リファクタリングの安全性が向上（カラム名変更時にコンパイラが全箇所を検出）
- IDEの補完が効くため、開発効率が向上

### 3. DSL vs DAO の二つのアプローチ

Exposedは用途に応じて2つのAPIを提供し、同一プロジェクト内で**併用可能**。

#### DSL (Domain-Specific Language)
**思想**: SQLライクな構文で完全な制御を提供

```kotlin
// 複雑なJOIN、集計、条件指定が得意
transaction {
    (Users innerJoin Cities)
        .slice(Users.name, Cities.name)
        .select { Users.active eq true }
        .orderBy(Users.name)
        .map { "User: ${it[Users.name]}, City: ${it[Cities.name]}" }
}
```

**利点**:
- 発行されるSQLを完全に制御
- 複雑なクエリ（JOIN、サブクエリ、集計）を柔軟に記述
- パフォーマンス最適化がしやすい

**欠点**:
- シンプルなCRUD操作でもコード量が多い

#### DAO (Data Access Object)
**思想**: Active Recordパターン、オブジェクト指向的な操作

```kotlin
// シンプルなCRUD操作が簡潔
transaction {
    val user = User.new {
        name = "Alice"
        age = 30
    }

    user.name = "Bob" // 自動でUPDATE
    user.delete()     // 自動でDELETE
}
```

**利点**:
- CRUD操作が簡潔
- ビジネスロジックに集中しやすい
- オブジェクト指向的で直感的

**欠点**:
- 裏で発行されるクエリが見えにくい
- N+1問題を引き起こしやすい
- 複雑なクエリは記述困難

### 4. 強制的なトランザクション管理

**すべてのDB操作は必ず `transaction` ブロック内で実行する**。これはExposedの絶対的なルール。

```kotlin
// GOOD: transactionブロック内で実行
fun createUser(name: String, cityName: String) {
    transaction {
        val cityId = Cities.select { Cities.name eq cityName }.single()[Cities.id]
        Users.insert {
            it[Users.name] = name
            it[Users.cityId] = cityId
        }
    }
}

// BAD: transactionブロックの外でDB操作
// これは `IllegalStateException: No transaction in context.` を引き起こす
fun getCityId(city: String): Int {
    return Cities.select { Cities.name eq city }.single()[Cities.id]
}
```

**トランザクションの自動管理**:
- ブロックが正常終了 → 自動コミット
- 例外が発生 → 自動ロールバック
- コネクションの自動解放（リソースリーク防止）

**Coroutinesとの統合**:

```kotlin
// GOOD: 非同期処理では newSuspendedTransaction を使用
suspend fun countUsers(): Long {
    return newSuspendedTransaction {
        Users.selectAll().count()
    }
}

// BAD: ブロッキングする transaction をCoroutine内で使用
// スレッドをブロックし、Coroutineの利点を損なう
suspend fun countUsersBlocking(): Long {
    return transaction { // 非効率
        Users.selectAll().count()
    }
}
```

**なぜ重要か**:
- リソース管理をフレームワークに委譲
- コネクションリーク、データ不整合を防止
- コードがクリーンになり、手動でのコミット/ロールバックが不要

## アンチパターン

### トランザクション外でのDB操作（最も多いAIの誤用）

AIは、ロジックを複数の関数に分割する際、各関数がトランザクションコンテキスト内で呼び出されることを忘れがち。

```kotlin
// ❌ BAD: DB操作を行う関数をtransactionの外で定義し、そのまま呼び出そうとする
class UserService {
    // この関数は内部でDBにアクセスするが、transactionでラップされていない
    fun findUser(id: Int): ResultRow? {
        // 呼び出し元がtransaction内にいるかどうかが不明
        return Users.select { Users.id eq id }.firstOrNull()
    }
}

// service.findUser(1) // IllegalStateException: No transaction in context.

// ✅ GOOD: DB操作を伴う関数はsuspendにし、関数内でトランザクション管理
class BetterUserService {
    suspend fun findUser(id: Int): ResultRow? {
        return newSuspendedTransaction {
            Users.select { Users.id eq id }.firstOrNull()
        }
    }
}

// ✅ GOOD: レポジトリパターンで明示的に規約を設定
interface UserRepository {
    fun findById(id: Int): ResultRow? // 実装はtransaction内で行われる
}

class ExposedUserRepository : UserRepository {
    override fun findById(id: Int): ResultRow? {
        // このクラスのメソッドは必ずtransaction内で呼び出されるという規約
        return Users.select { Users.id eq id }.firstOrNull()
    }
}

// 呼び出し側
transaction {
    val repo = ExposedUserRepository()
    repo.findById(1)
}
```

**なぜ重要か**: Exposedの設計思想の根幹。トランザクションの欠落は確実な実行時エラーにつながる。

### N+1クエリ問題（DAOでの遅延ロード誤用）

DAO APIでは、関連オブジェクトへのアクセスがデフォルトで**遅延ロード**される。AIはこの挙動を意識せず、ループ内でアクセスしがち。

```kotlin
// テーブル定義
object Users : IntIdTable() {
    val name = varchar("name", 50)
    val cityId = reference("city_id", Cities)
}

object Cities : IntIdTable() {
    val name = varchar("name", 50)
}

// DAO Entity
class User(id: EntityID<Int>) : IntEntity(id) {
    companion object : IntEntityClass<User>(Users)
    var name by Users.name
    var city by City referencedOn Users.cityId
}

class City(id: EntityID<Int>) : IntEntity(id) {
    companion object : IntEntityClass<City>(Cities)
    var name by Cities.name
}

// ❌ BAD: AIが生成しがちなコード。一見問題なさそうに見えるが、パフォーマンスの罠
transaction {
    User.all().forEach { user -> // 1. 全ユーザーを取得 (1クエリ)
        // 2. このアクセスで、ユーザーごとに city を取得 (Nクエリ)
        println("${user.name} lives in ${user.city.name}") // N+1問題
    }
}
// 発行されるクエリ: 1 + N回 (ユーザー数が100なら101回)

// ✅ GOOD: Eager Loadingを明示的に使用
transaction {
    User.all().with(User::city).forEach { user ->
        // cityは既に読み込まれているため、追加のクエリは発行されない
        println("${user.name} lives in ${user.city.name}")
    }
}
// 発行されるクエリ: 2回（Users取得で1回、Cities取得で1回）
```

**より複雑な例（ネストした関連）**:

```kotlin
// ❌ BAD: 多段階のN+1問題
transaction {
    User.all().forEach { user ->
        println("${user.name}: ${user.posts.count()}") // N+1
        user.posts.forEach { post ->
            println("  ${post.title}: ${post.comments.count()}") // N+1のN+1
        }
    }
}

// ✅ GOOD: ネストした関連も一括ロード
transaction {
    User.all()
        .with(User::posts)
        .forEach { user ->
            println("${user.name}: ${user.posts.count()}")
            user.posts.with(Post::comments).forEach { post ->
                println("  ${post.title}: ${post.comments.count()}")
            }
        }
}
```

**load() vs with()**:
- `load()`: 単一エンティティの関連を事後ロード
- `with()`: コレクション全体の関連を一括ロード（より推奨）

```kotlin
// load(): 単一エンティティ
transaction {
    val film = StarWarsFilm.findById(1)
        .load(StarWarsFilm::actors) // actorsを追加で読み込む
}

// with(): コレクション全体（より効率的）
transaction {
    StarWarsFilm.all().with(StarWarsFilm::actors)
}
```

**なぜ重要か**: データ量が増えるにつれてレスポンスタイムが劇的に悪化。100件のデータなら101回のクエリが発行される。

### 過剰な抽象化

JPAの経験を持つ開発者やAIは、Exposedの上にさらに独自のGeneric DAOパターンを構築しようとすることがある。

```kotlin
// ❌ BAD: 過剰な抽象化。Exposedの柔軟性を損なう
interface GenericRepository<T, ID> {
    fun findById(id: ID): T?
    fun save(entity: T): T
    fun findAll(): List<T>
}

// この抽象化は、Exposedの柔軟なDSLクエリの妨げになる
// 例: 特定のクエリでJOINやsliceを使いたい場合、インターフェースで表現しにくい

class UserRepositoryImpl : GenericRepository<User, Int> {
    // Exposedの強力なDSL機能を使えない制約
}

// ✅ GOOD: Exposedの機能に特化した具体的なレポジトリ
class UserRepository {
    // この関数はtransaction内で呼び出されることを前提
    fun findUserDetails(id: Int): UserDetailsDTO? {
        return Users.leftJoin(Cities)
            .slice(Users.name, Cities.name)
            .select { Users.id eq id }
            .map { UserDetailsDTO(it[Users.name], it[Cities.name]) }
            .firstOrNull()
    }

    fun findActiveUsers(): List<User> {
        return User.find { Users.active eq true }.toList()
    }

    // 複雑なレポート用クエリも柔軟に記述
    fun getUserStatsByCity(): List<CityStats> {
        return Users.innerJoin(Cities)
            .slice(Cities.name, Users.id.count())
            .selectAll()
            .groupBy(Cities.name)
            .map { CityStats(it[Cities.name], it[Users.id.count()]) }
    }
}

data class UserDetailsDTO(val userName: String, val cityName: String)
data class CityStats(val cityName: String, val userCount: Long)
```

**なぜ重要か**:
- Exposedの主な利点は「型安全性を保ちながらSQLに近い柔軟なクエリ」
- 過剰な抽象化はこの柔軟性を覆い隠し、Exposedを使うメリットを失わせる
- シンプルなCRUDはDAO、複雑なクエリはDSLを使った特化レポジトリ関数というハイブリッドアプローチが効果的

### SELECT * の多用

```kotlin
// ❌ BAD: テーブルの全カラムを取得
transaction {
    Users.selectAll().forEach {
        println("Name: ${it[Users.name]}")
    }
}

// ✅ GOOD: 必要なカラムだけを明示的に指定
transaction {
    Users.slice(Users.name).selectAll().forEach {
        println("Name: ${it[Users.name]}")
    }
}
```

**なぜ重要か**:
- 不要なデータ転送を避け、ネットワーク帯域とメモリを節約
- 特に大きなテーブルやBLOB/TEXT型を含むテーブルで効果が大きい

## シニアエンジニアの判断基準

### DSL vs DAO の選択

| ケース | 推奨 | 理由 |
|--------|------|------|
| 基本的なCRUDエンドポイント | DAO | コードが簡潔。`User.new { ... }`, `user.delete()` |
| 複数テーブルのJOIN | DSL | 完全な制御。複雑なクエリを柔軟に記述 |
| 統計・集計クエリ | DSL | `count`, `sum`, `avg` などの集計関数が使いやすい |
| レポート画面 | DSL | 複雑な条件、ソート、グループ化を明示的に記述 |
| バッチ処理 | DSL | `batchInsert`, 一括更新が効率的 |
| 単一オブジェクト操作 | DAO | オブジェクト指向的で直感的 |
| パフォーマンス最適化が必要 | DSL | 発行されるSQLを完全に制御可能 |

### ハイブリッドアプローチ（推奨）

```kotlin
// 基本的なアクセス層はDAOで簡潔に
class UserService {
    suspend fun createUser(name: String, age: Int): User {
        return newSuspendedTransaction {
            User.new {
                this.name = name
                this.age = age
            }
        }
    }

    suspend fun findById(id: Int): User? {
        return newSuspendedTransaction {
            User.findById(id)
        }
    }

    // 複雑なクエリは内部的にDSLを使用
    suspend fun findActiveUsersWithCity(): List<UserCityDTO> {
        return newSuspendedTransaction {
            (Users innerJoin Cities)
                .slice(Users.name, Users.age, Cities.name)
                .select { Users.active eq true }
                .orderBy(Users.name)
                .map {
                    UserCityDTO(
                        userName = it[Users.name],
                        userAge = it[Users.age],
                        cityName = it[Cities.name]
                    )
                }
        }
    }
}
```

### トランザクション境界の設計

| パターン | 推奨 | 理由 |
|---------|------|------|
| コントローラー層でtransaction | ❌ | ビジネスロジックとDBアクセスが分離できない |
| サービス層でtransaction | ✅ | ビジネスロジックの単位でトランザクション管理 |
| リポジトリ層でtransaction | ✅ | DB操作を確実にトランザクション内で実行 |
| 関数ごとに個別transaction | △ | 細かすぎる場合、複数DB操作の一貫性が保てない |

```kotlin
// ✅ GOOD: サービス層でトランザクション境界を管理
class UserService {
    suspend fun registerUser(name: String, cityName: String) {
        newSuspendedTransaction {
            // 一連のビジネスロジックを1つのトランザクションで
            val city = City.find { Cities.name eq cityName }.firstOrNull()
                ?: City.new { this.name = cityName }

            User.new {
                this.name = name
                this.city = city
            }

            // どこかで例外が発生すれば、全体がロールバック
        }
    }
}
```

### JPA/Hibernate との使い分け

| 観点 | JPA/Hibernate | Exposed |
|------|---------------|---------|
| **思想** | 完全なORM。DBを隠蔽 | 軽量SQL-Builder。SQLを制御 |
| **学習コスト** | 初期は低い、最適化は難しい | SQLの知識が必要 |
| **パフォーマンス** | キャッシュが効けば高速 | オーバーヘッドが少ない |
| **クエリ制御** | JPQLで抽象化 | SQLに近く、完全制御 |
| **Kotlinとの親和性** | Java中心の設計 | Kotlin専用設計 |
| **選択基準** | Spring/Javaエコシステム | Ktor/Kotlin中心のプロジェクト |

**Exposedを選択すべき場合**:
- Kotlin中心のプロジェクト（Ktor、Kotlin Multiplatform）
- SQLを直接制御し、細かくパフォーマンス最適化したい
- 軽量なフレームワークを好む
- ORMの「魔法」を避けたい

**JPA/Hibernateを選択すべき場合**:
- Javaエコシステム（特にSpring Framework）に深く依存
- チームがJPAに習熟している
- 複雑なドメインモデルとキャッシュの恩恵が大きい
- データベースに依存しないポータビリティが重要

## 参考資料

### 公式ドキュメント
- [Exposed Wiki](https://github.com/JetBrains/Exposed/wiki)
- [DSL and DAO](https://github.com/JetBrains/Exposed/wiki/DSL-and-DAO)
- [Schema Definition](https://github.com/JetBrains/Exposed/wiki/Schema-Definition)
- [Transactions](https://github.com/JetBrains/Exposed/wiki/Transactions)
- [DAO API - Eager Loading](https://github.com/JetBrains/Exposed/wiki/DAO#eager-loading)

### 実践的な記事
- [Getting Started with Exposed](https://www.baeldung.com/kotlin/exposed)
- [Kotlin Exposed vs. Spring Data JPA: A Performance Comparison](https://medium.com/making-waves/kotlin-exposed-vs-spring-data-jpa-a-performance-comparison-17444c15d48a)
- [Why We Chose Kotlin Exposed Over JPA for Our New Microservice](https://betterprogramming.pub/why-we-chose-kotlin-exposed-over-jpa-for-our-new-microservice-60372898b71d)
- [Exposed ORM: Solving N+1 problem](https://medium.com/@k.topolski/exposed-orm-solving-n-1-problem-51a773223067)
- [A comprehensive guide to Kotlin Exposed: DAO and DSL](https://dev.to/zeno001/a-comprehensive-guide-to-kotlin-exposed-dao-and-dsl-368c)
