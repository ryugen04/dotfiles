# Kotlin Philosophy

Kotlin の設計思想とシニアエンジニアが守るべき原則。

## 核心思想

### 1. Null安全性

Kotlinの最重要機能。コンパイル時にnullチェックを強制し、実行時の `NullPointerException` を防ぐ。

```kotlin
// 型システムでnullableとnon-nullableを明確に区別
val nonNullable: String = "Hello"  // nullは代入不可
val nullable: String? = null       // nullを許容

// BAD: Javaスタイルの冗長なnullチェック
fun processValue(value: String?) {
    if (value != null) {
        println("Length: ${value.length}")
    }
}

// GOOD: セーフコール演算子とエルビス演算子
fun processValue(value: String?) {
    // ?. はnullの場合にnullを返し、エルビス演算子 ?: でデフォルト値を提供
    println("Length: ${value?.length ?: 0}")
}

// GOOD: letスコープ関数でnullでない場合のみ処理
fun processValue(value: String?) {
    value?.let {
        // itでvalueにアクセス（nullでない場合のみ実行）
        println("Length: ${it.length}")
    }
}
```

**なぜ重要か**: Javaで最も多い実行時エラー `NullPointerException` をコンパイル時に検出。Googleの調査では、Androidアプリのクラッシュの70%がNPEによるものだった。

### 2. 不変性優先 (val > var)

不変データを優先し、状態変更による予期せぬバグを防ぐ。

```kotlin
// BAD: 不必要なvar（可変変数）
fun calculateTotal(items: List<Int>): Int {
    var total = 0  // 再代入が必要だが、スコープを狭められる
    for (item in items) {
        total += item
    }
    return total
}

// GOOD: 関数型スタイルで不変性を保つ
fun calculateTotal(items: List<Int>): Int {
    return items.sum()  // 中間変数なしで計算
}

// GOOD: 必要な場合もvalで宣言できるか検討
fun greet(name: String) {
    val greeting = "Hello, $name"  // 再代入不要なのでval
    println(greeting)
}

// コレクションも読み取り専用を優先
// BAD: すぐにミュータブルコレクションを使う
val numbers = mutableListOf(1, 2, 3)

// GOOD: 読み取り専用コレクション（変更が必要な場合のみMutableを使う）
val numbers: List<Int> = listOf(1, 2, 3)
```

**Kotlin公式の原則**: 「ローカル変数とプロパティは、初期化後に変更されない場合、常に `var` ではなく `val` で宣言する」

### 3. データクラスの活用

DTOやPOJOのボイラープレートコードを自動生成する。

```kotlin
// BAD: Javaスタイルの冗長なクラス定義
class Customer(private val name: String, private val email: String) {
    fun getName() = name
    fun getEmail() = email

    override fun equals(other: Any?): Boolean { /* ... */ }
    override fun hashCode(): Int { /* ... */ }
    override fun toString(): String { /* ... */ }
    fun copy(name: String = this.name, email: String = this.email) { /* ... */ }
}

// GOOD: data classで1行
data class Customer(val name: String, val email: String)
// 自動生成: equals(), hashCode(), toString(), copy(), componentN()
```

**自動生成される機能**:
- `equals()` / `hashCode()`: 値による等価性比較
- `toString()`: 読みやすい文字列表現
- `copy()`: イミュータブルな更新
- `componentN()`: 分解宣言

### 4. sealed classによる型安全なパターンマッチ

制限された型階層で、すべてのケースを漏れなく処理する。

```kotlin
// sealed classで可能な状態を制限
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
    data object Loading : Result<Nothing>()
}

// GOOD: whenで網羅性チェック（elseが不要）
fun <T> handleResult(result: Result<T>) {
    when (result) {
        is Result.Success -> println("Data: ${result.data}")
        is Result.Error -> println("Error: ${result.exception.message}")
        is Result.Loading -> println("Loading...")
        // 新しいサブクラスを追加するとコンパイルエラーになる（安全）
    }
}

// BAD: enum では値を持てない
enum class Status { SUCCESS, ERROR, LOADING }  // データを保持できない

// BAD: open classでは網羅性チェックができない
open class Result
class Success(val data: String) : Result()
class Error(val msg: String) : Result()
// 他のファイルで新しいサブクラスを追加できてしまう
```

**なぜ重要か**: 代数的データ型のような型安全性を持ち、コンパイラが全ケースの処理を強制する。状態管理やAPIレスポンスのモデリングに最適。

### 5. スマートキャスト

型チェック後、明示的なキャストが不要。

```kotlin
// BAD: Javaスタイルの明示的キャスト
fun process(obj: Any) {
    if (obj is String) {
        println((obj as String).length)  // 不要なキャスト
    }
}

// GOOD: スマートキャストで自動的に型が変換される
fun process(obj: Any) {
    if (obj is String) {
        println(obj.length)  // objは自動的にStringとして扱われる
    }
}

// GOOD: whenでもスマートキャストが機能
fun describe(obj: Any): String = when (obj) {
    is Int -> "Int: ${obj + 1}"           // objはInt型
    is String -> "String: ${obj.length}"  // objはString型
    is IntArray -> "Array: ${obj.sum()}"  // objはIntArray型
    else -> "Unknown"
}
```

### 6. 拡張関数

既存クラスを継承せずに機能を追加する。

```kotlin
// GOOD: 標準ライブラリの型に機能を追加
fun String.addExclamation(): String = this + "!"

val greeting = "Hello".addExclamation()  // "Hello!"

// GOOD: nullableな型にも拡張関数を定義可能
fun String?.orEmpty(): String = this ?: ""

val result: String? = null
println(result.orEmpty())  // "" (空文字列)

// BAD: 過剰な拡張関数（クラス内部に定義すべき）
fun User.validateEmail(): Boolean { /* ... */ }  // Userクラスのメソッドとして定義すべき

// GOOD: ユーティリティ的な操作に限定
fun String.toSnakeCase(): String =
    this.replace(Regex("([a-z])([A-Z])"), "$1_$2").lowercase()
```

**使用指針**:
- 外部ライブラリの型に機能を追加する場合
- ドメイン横断的なユーティリティ関数
- DSLの構築

**避けるべき**:
- クラス内部で定義すべきビジネスロジック
- 過度な使用による名前空間の汚染

### 7. コルーチンによる構造化された並行性

非同期処理を同期的に書け、ライフサイクルに紐づいた自動キャンセルを提供。

```kotlin
// BAD: スレッドベースの非同期処理（リソースリーク）
fun fetchData() {
    Thread {
        // ネットワークリクエスト
        // アクティビティが破棄されてもスレッドは動き続ける
    }.start()
}

// GOOD: コルーチンで構造化された並行性
class MyViewModel : ViewModel() {
    fun fetchData() {
        viewModelScope.launch {
            // ViewModelがクリアされると自動的にキャンセル
            val data = withContext(Dispatchers.IO) {
                // ネットワークリクエスト
            }
            updateUI(data)
        }
    }
}

// GOOD: 並行実行とエラーハンドリング
suspend fun loadUserData(userId: String): UserData = coroutineScope {
    val userDeferred = async { fetchUser(userId) }
    val postsDeferred = async { fetchPosts(userId) }

    // 両方の結果を待つ（並行実行）
    UserData(
        user = userDeferred.await(),
        posts = postsDeferred.await()
    )
    // いずれかが失敗すると、もう一方も自動キャンセル
}
```

**構造化された並行性の利点**:
- メモリリークの防止（スコープに紐づく）
- 自動キャンセル（親がキャンセルされると子も停止）
- エラー伝播（子の例外が親に伝わる）

## アンチパターン

### !! 演算子の乱用（最も危険）

`!!` (non-null assertion) はKotlinのNull安全性を無効化する。

```kotlin
// ❌ BAD: !!演算子は実質的にNullPointerExceptionを呼び込む
fun printUserName(user: User?) {
    println(user!!.name)  // userがnullならクラッシュ
}

// ✅ GOOD: セーフコール + エルビス演算子
fun printUserName(user: User?) {
    println(user?.name ?: "Unknown")
}

// ✅ GOOD: early returnでnullチェック
fun printUserName(user: User?) {
    val name = user?.name ?: return
    println(name)  // nameは非null
}

// !! が許される唯一のケース: コンパイラが検出できないがロジック的に確実
fun example() {
    var value: String? = null
    value = "initialized"
    // コンパイラは value がnullでないと推論できないが、ロジック的に確実
    println(value!!.length)  // ただしこの場合もletなどで回避すべき
}
```

**原則**: `!!` を書く場合は必ず「なぜnullでないと言い切れるか」をコメントで説明する。基本的には使わない。

### var の多用

```kotlin
// ❌ BAD: 不必要なvar
fun greet(firstName: String, lastName: String) {
    var fullName = "$firstName $lastName"  // 再代入されない
    println("Hello, $fullName")
}

// ✅ GOOD: valで宣言
fun greet(firstName: String, lastName: String) {
    val fullName = "$firstName $lastName"
    println("Hello, $fullName")
}

// ❌ BAD: ループ変数にvar
fun sumPositive(numbers: List<Int>): Int {
    var sum = 0
    for (num in numbers) {
        if (num > 0) sum += num
    }
    return sum
}

// ✅ GOOD: 関数型スタイル
fun sumPositive(numbers: List<Int>): Int {
    return numbers.filter { it > 0 }.sum()
}
```

### GlobalScopeの使用（メモリリーク）

```kotlin
// ❌ BAD: GlobalScopeはライフサイクルを無視
class MyActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        GlobalScope.launch {
            // Activityが破棄されてもコルーチンは動き続ける
            delay(10000L)
            updateUI()  // メモリリーク or クラッシュ
        }
    }
}

// ✅ GOOD: ライフサイクルに対応したスコープ
class MyActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        lifecycleScope.launch {
            // Activityが破棄されると自動キャンセル
            delay(10000L)
            updateUI()
}
    }
}

// ✅ GOOD: ViewModelスコープ
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch {
            // ViewModelがクリアされると自動キャンセル
        }
    }
}
```

### 過剰なスコープ関数のネスト

```kotlin
// ❌ BAD: ネストが深く、thisとitが混乱
user?.let {
    it.address?.let { addr ->
        addr.city?.let { city ->
            println(city.uppercase())
        }
    }
}

// ✅ GOOD: チェーンでフラットに
user?.address?.city?.let { city ->
    println(city.uppercase())
}

// ✅ GOOD: early returnで明確に
fun printCity(user: User?) {
    val city = user?.address?.city ?: return
    println(city.uppercase())
}
```

### whenでelseを省略（sealed class以外）

```kotlin
// ❌ BAD: 将来の拡張でバグの原因
fun handle(status: Int) {
    when (status) {
        200 -> println("OK")
        404 -> println("Not Found")
        // elseがないため、他のステータスコードが来ると何も起こらない
    }
}

// ✅ GOOD: elseで予期しないケースを処理
fun handle(status: Int) {
    when (status) {
        200 -> println("OK")
        404 -> println("Not Found")
        else -> println("Unknown status: $status")
    }
}

// ✅ GOOD: sealed classなら網羅性チェックでelseが不要
sealed class Status {
    object OK : Status()
    object NotFound : Status()
}

fun handle(status: Status) {
    when (status) {
        is Status.OK -> println("OK")
        is Status.NotFound -> println("Not Found")
        // 新しいサブクラスを追加するとコンパイルエラー
    }
}
```

### Sequenceを使わない大規模コレクション処理

```kotlin
val words = (1..1_000_000).map { "word$it" }

// ❌ BAD: 中間リストが大量に生成される（メモリ無駄）
val result = words
    .filter { it.length > 5 }      // 中間リスト生成
    .map { it.uppercase() }         // 中間リスト生成
    .take(10)

// ✅ GOOD: Sequenceで遅延評価（必要な分だけ処理）
val result = words.asSequence()
    .filter { it.length > 5 }
    .map { it.uppercase() }
    .take(10)                       // ここまで何も実行されない
    .toList()                       // ここで初めて実行
```

## シニアエンジニアの判断基準

### スコープ関数の選択

| スコープ関数 | オブジェクト参照 | 戻り値 | 主な用途 |
|------------|---------------|-------|---------|
| `let` | `it` | ラムダ結果 | null安全な処理、変換処理 |
| `apply` | `this` | オブジェクト自身 | オブジェクトの初期化・設定 |
| `run` | `this` | ラムダ結果 | 初期化 + 計算結果の取得 |
| `also` | `it` | オブジェクト自身 | 副作用的な処理（ログなど） |
| `with` | `this` | ラムダ結果 | 同一オブジェクトへの複数操作 |

```kotlin
// let: null安全な操作と変換
val length: Int? = nullableString?.let {
    println("Processing: $it")
    it.length
}

// apply: オブジェクトの初期化
val person = Person().apply {
    name = "Taro"
    age = 30
}

// run: 初期化 + 結果の計算
val greeting = person.run {
    "Hello, I'm $name, $age years old"
}

// also: デバッグ・ログ（チェーンの途中で副作用）
val result = numbers
    .filter { it > 0 }
    .also { println("Filtered: $it") }
    .map { it * 2 }

// with: 同一オブジェクトへの複数操作
with(canvas) {
    drawCircle(x, y, radius)
    drawLine(x1, y1, x2, y2)
}
```

### コレクションの選択

| 要件 | 推奨型 | 理由 |
|------|-------|------|
| 読み取り専用リスト | `List<T>` | 不変性を保証、予期せぬ変更を防ぐ |
| 変更可能リスト | `MutableList<T>` | 明示的に変更可能と示す |
| 重複を許さない | `Set<T>` | 一意性を保証 |
| キー・バリュー | `Map<K, V>` | 高速な検索 |
| 大規模データの遅延処理 | `Sequence<T>` | メモリ効率が良い |
| 順序付きマップ | `LinkedHashMap<K, V>` | 挿入順を保持 |

### Null処理の選択

| 状況 | 推奨アプローチ | 例 |
|------|-------------|---|
| デフォルト値を提供 | エルビス演算子 `?:` | `value ?: "default"` |
| nullの場合にスキップ | セーフコール `?.` | `user?.name` |
| nullの場合のみ処理 | `?.let { }` | `name?.let { print(it) }` |
| 確実にnull以外に変換 | `requireNotNull()` | `requireNotNull(user)` |
| 確実にnon-nullと断言 | `checkNotNull()` | `checkNotNull(config)` |

### コルーチンスコープの選択

| スコープ | 用途 | キャンセルタイミング |
|---------|------|-------------------|
| `viewModelScope` | ViewModelでのデータ取得 | ViewModelがクリアされた時 |
| `lifecycleScope` | Activity/Fragmentの処理 | ライフサイクルが破棄された時 |
| `GlobalScope` | ❌ 使用禁止 | キャンセルされない（リーク） |
| `coroutineScope` | カスタムsuspend関数内 | 親コルーチンと同じ |
| `supervisorScope` | 子の失敗を伝播させない | 親コルーチンと同じ |

## Kotlin Idioms（慣用的パターン）

### 文字列テンプレート

```kotlin
// BAD: 文字列連結
val greeting = "Hello, " + name + "!"

// GOOD: 文字列テンプレート
val greeting = "Hello, $name!"

// GOOD: 式の埋め込み
val message = "Length is ${name.length}"
```

### 名前付き引数

```kotlin
// BAD: 位置引数（可読性が低い）
createUser("Taro", "taro@example.com", 30, true)

// GOOD: 名前付き引数で明確に
createUser(
    name = "Taro",
    email = "taro@example.com",
    age = 30,
    isActive = true
)
```

### 分解宣言

```kotlin
// GOOD: data classの分解宣言
val (name, email) = customer

// GOOD: Pairの分解
val (key, value) = map.entries.first()

// GOOD: ループでの分解
for ((index, item) in list.withIndex()) {
    println("$index: $item")
}
```

### 関数リテラルとラムダ

```kotlin
// GOOD: 最後の引数がラムダなら括弧の外に
list.filter { it > 0 }

// GOOD: 引数が1つならit
list.map { it * 2 }

// GOOD: 使わない引数はアンダースコア
map.forEach { (_, value) -> println(value) }
```

### デフォルト引数とオーバーロード

```kotlin
// BAD: 複数のオーバーロード
fun connect(host: String) = connect(host, 80)
fun connect(host: String, port: Int) = connect(host, port, 30)
fun connect(host: String, port: Int, timeout: Int) { /* ... */ }

// GOOD: デフォルト引数で1つの関数
fun connect(host: String, port: Int = 80, timeout: Int = 30) {
    // ...
}
```

## Javaとの比較

### Javaから移行する理由

| Javaの問題 | Kotlinの解決策 | 効果 |
|-----------|-------------|------|
| NullPointerException | Null安全性 | 実行時エラーの70%削減 |
| ボイラープレート | data class, プロパティ | コード量40%削減 |
| 冗長なコールバック | コルーチン | 非同期コードの可読性向上 |
| 拡張性の低さ | 拡張関数 | 継承なしで機能追加 |
| チェック例外 | チェック例外なし | 例外処理の簡素化 |

### 移行パターン

```kotlin
// Java
public class User {
    private final String name;
    private int age;

    public User(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String getName() { return name; }
    public int getAge() { return age; }
    public void setAge(int age) { this.age = age; }
}

// Kotlin (1行で同等の機能)
data class User(val name: String, var age: Int)
```

## 参考資料

- [Kotlin Coding Conventions](https://kotlinlang.org/docs/coding-conventions.html)
- [Kotlin Idioms](https://kotlinlang.org/docs/idioms.html)
- [API Guidelines - Kotlin](https://kotlinlang.org/docs/api-guidelines-introduction.html)
- [Scope Functions](https://kotlinlang.org/docs/scope-functions.html)
- [Null Safety](https://kotlinlang.org/docs/null-safety.html)
- [Coroutines Best Practices (Android)](https://developer.android.com/kotlin/coroutines/coroutines-best-practices)
- [Type Safety and Smart Casts](https://kotlinlang.org/docs/typecasts.html)
