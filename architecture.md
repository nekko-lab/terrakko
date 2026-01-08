# Terrakko Architecture Documentation

## 概要

TerrakkoはDiscord.jsを使用したTypeScript製のDiscord Botアプリケーションです。Proxmox VE APIを通じてVM（仮想マシン）の作成・管理を行い、ユーザーがDiscord上で簡単にVMを操作できるようにします。

## 技術スタック

- **言語**: TypeScript
- **ランタイム**: Node.js 18+
- **Discordライブラリ**: Discord.js v14
- **データベース**: SQLite (better-sqlite3)
- **HTTPクライアント**: Axios
- **テストフレームワーク**: Jest + ts-jest
- **環境変数管理**: dotenv

## アーキテクチャ概要

Terrakkoは**レイヤードアーキテクチャ**を採用しており、以下の層で構成されています:

1. **Presentation Layer (UI)**: Discord UI コンポーネント（Embed、Button、Select Menu）
2. **Application Layer (Bot/Commands)**: Discordイベント処理とルーティング
3. **Domain Layer**: ビジネスロジック（VM、User、Session管理）
4. **Infrastructure Layer**: 外部システムとの通信（Proxmox API、Database）
5. **Utilities Layer**: 共通ユーティリティ（Logger、Validator、Time）

## システムアーキテクチャ図

```mermaid
graph TB
    subgraph "Discord Client"
        DC[Discord User]
    end

    subgraph "Presentation Layer"
        UI[UI Components]
        EB[EmbedBuilder]
        MB[MenuBuilder]
        CF[ComponentFactory]
    end

    subgraph "Application Layer"
        TB[TerrakkoBot]
        IR[InteractionRouter]
        MC[MenuCommand]
    end

    subgraph "Domain Layer"
        VS[VMService]
        US[UserService]
        SM[SessionManager]
        VM[VM Entity]
        U[User Entity]
        S[Session Entity]
    end

    subgraph "Infrastructure Layer"
        PC[ProxmoxClient]
        PVA[ProxmoxVMAdapter]
        DB[DatabaseManager]
        UD[UserDAO]
        CFG[Config]
    end

    subgraph "Utilities"
        LOG[Logger]
        VAL[Validator]
        TIME[Time]
    end

    subgraph "External Systems"
        PVE[Proxmox VE API]
        SQLITE[SQLite Database]
    end

    DC -->|Messages/Interactions| TB
    TB --> IR
    TB --> MC
    IR --> VS
    IR --> US
    IR --> SM
    IR --> UI
    MC --> UI

    VS --> PVA
    VS --> US
    US --> UD
    US --> PC

    PVA --> PC
    PC --> PVE

    UD --> DB
    DB --> SQLITE

    UI --> EB
    UI --> MB
    UI --> CF

    VS --> VM
    US --> U
    SM --> S

    TB --> CFG
    VS --> CFG
    US --> CFG
    PC --> CFG

    TB --> LOG
    IR --> LOG
    VS --> LOG
    US --> LOG
    PC --> LOG

    IR --> VAL
    VS --> VAL
    U --> VAL
```

## クラス依存関係図

```mermaid
classDiagram
    class TerrakkoBot {
        -Client client
        -InteractionRouter interactionRouter
        -MenuCommand menuCommand
        -VMService vmService
        -UserService userService
        -ProxmoxClient proxmoxClient
        +login()
        +destroy()
        -onReady()
        -onMessage()
        -onInteraction()
    }

    class InteractionRouter {
        -VMService vmService
        -UserService userService
        -SessionManager sessionManager
        +handle(Interaction)
        -handleButton()
        -handleModal()
        -handleSelectMenu()
        -handlePowerControl()
        -handleConfirmButton()
    }

    class MenuCommand {
        -UserService userService
        +execute(Message)
    }

    class VMService {
        -VMAdapter vmAdapter
        -UserService userService
        +createVM(params)
        +deleteVM(vmid, ownerId)
        +listUserVMs(userId)
        +powerOn(vmid)
        +shutdown(vmid)
        +reboot(vmid)
        +stop(vmid)
        +checkVMNameExists(name)
    }

    class UserService {
        -UserDAO userDAO
        -ProxmoxClient proxmoxClient
        +registerUser(user)
        +getUser(discordId)
        +updateUser(user)
        +ensureUserExists(discordId)
        +userExists(discordId)
        -generateTagId(username)
    }

    class SessionManager {
        -Map~string, Session~ sessions
        +create(userId)
        +get(sessionId)
        +getLatestSessionByUser(userId)
        +delete(sessionId)
        +cleanup()
    }

    class ProxmoxClient {
        -AxiosInstance axiosInstance
        -string region
        -number tempId
        +initialize()
        +get(path)
        +post(path, data)
        +put(path, data)
        +delete(path)
        +createTag(tagId, description)
        +getRegion()
        +getTempId()
    }

    class ProxmoxVMAdapter {
        -ProxmoxClient client
        +cloneTemplate(vmid, name, username, password, sshKey, tagId)
        +deleteVM(region, vmid)
        +getStatus(region, vmid)
        +listVMs(region)
        +getNextVMID()
        +startVM(region, vmid)
        +stopVM(region, vmid)
        +shutdownVM(region, vmid)
        +rebootVM(region, vmid)
        +checkVMNameExists(name)
    }

    class UserDAO {
        -Database db
        +insert(discordId, username, password, sshkey, discordUsername, tagId)
        +update(discordId, username, password, sshkey, discordUsername, tagId)
        +get(discordId)
        +exists(discordId)
        +delete(discordId)
    }

    class DatabaseManager {
        -Database db
        +getInstance()
        +initialize()
        +close()
        +getDB()
    }

    class VM {
        +number vmId
        +string name
        +string ownerId
        +Region region
        +VMStatus status
        +string hostname
        +string ipv4
        +string ipv6
        +isOwner(userId)
        +isRunning()
        +isStopped()
    }

    class User {
        +string discordId
        +string username
        +string password
        +string sshPublicKey
        +string discordUsername
        +string proxmoxTagId
        +isValid()
    }

    class Session {
        +string id
        +string userId
        +number createdAt
        +Map data
        +set(key, value)
        +get(key)
        +isExpired()
    }

    class Config {
        +string VERSION
        +string DOMAIN
        +number TIME
        +string PVE_HOST
        +string PVE_USER
        +string PVE_TOKEN
        +string PVE_SECRET
        +string[] PVE_REGION
        +number[] PVE_TEMP_ID
        +string DIS_TOKEN
        +number DIS_CHANNEL_ID
        +validate()
        -parseJsonEnv(key, defaultValue)
    }

    class Validator {
        +isValidVMID(vmid)
        +isNotEmpty(value)
        +isValidSSHKey(key)
        +isValidCPU(cpu)
        +isValidMemory(memory)
        +isValidVMCount(count)
    }

    class Logger {
        +info(message)
        +error(message, error)
        +warn(message)
    }

    TerrakkoBot --> InteractionRouter
    TerrakkoBot --> MenuCommand
    TerrakkoBot --> VMService
    TerrakkoBot --> UserService
    TerrakkoBot --> ProxmoxClient
    TerrakkoBot --> Config
    TerrakkoBot --> Logger

    InteractionRouter --> VMService
    InteractionRouter --> UserService
    InteractionRouter --> SessionManager
    InteractionRouter --> Validator
    InteractionRouter --> Logger

    MenuCommand --> UserService

    VMService --> ProxmoxVMAdapter
    VMService --> UserService
    VMService --> VM
    VMService --> Config
    VMService --> Logger
    VMService --> Validator

    UserService --> UserDAO
    UserService --> ProxmoxClient
    UserService --> User
    UserService --> Config
    UserService --> Logger

    SessionManager --> Session

    ProxmoxVMAdapter --> ProxmoxClient

    ProxmoxClient --> Config
    ProxmoxClient --> Logger

    UserDAO --> DatabaseManager

    User --> Validator
```

## データフロー

### 1. VM作成フロー

```mermaid
sequenceDiagram
    actor User
    participant Discord
    participant TerrakkoBot
    participant InteractionRouter
    participant VMService
    participant UserService
    participant ProxmoxVMAdapter
    participant ProxmoxClient
    participant ProxmoxVE

    User->>Discord: trk! コマンド送信
    Discord->>TerrakkoBot: onMessage()
    TerrakkoBot->>MenuCommand: execute()
    MenuCommand->>Discord: メインメニュー表示

    User->>Discord: "Create VM" ボタンクリック
    Discord->>TerrakkoBot: onInteraction()
    TerrakkoBot->>InteractionRouter: handle()
    InteractionRouter->>Discord: VM数選択表示

    User->>Discord: VM数選択
    Discord->>InteractionRouter: handleSelectMenu()
    InteractionRouter->>Discord: VM名入力モーダル表示

    User->>Discord: VM名入力
    Discord->>InteractionRouter: handleModal()
    InteractionRouter->>UserService: getUser()
    UserService-->>InteractionRouter: User情報
    InteractionRouter->>VMService: checkVMNameExists()
    VMService-->>InteractionRouter: 重複チェック結果
    InteractionRouter->>Discord: 確認メッセージ表示

    User->>Discord: "Yes" ボタンクリック
    Discord->>InteractionRouter: handleConfirmButton()
    InteractionRouter->>VMService: createVM()
    VMService->>UserService: getUser()
    UserService-->>VMService: User情報
    VMService->>ProxmoxVMAdapter: cloneTemplate()
    ProxmoxVMAdapter->>ProxmoxClient: post(/nodes/.../qemu/.../clone)
    ProxmoxClient->>ProxmoxVE: API Request
    ProxmoxVE-->>ProxmoxClient: Response
    ProxmoxClient-->>ProxmoxVMAdapter: Result
    ProxmoxVMAdapter-->>VMService: VM作成完了
    VMService-->>InteractionRouter: VM[]
    InteractionRouter->>Discord: 成功メッセージ表示
```

### 2. ユーザー登録フロー

```mermaid
sequenceDiagram
    actor User
    participant Discord
    participant InteractionRouter
    participant UserService
    participant ProxmoxClient
    participant UserDAO
    participant Database

    User->>Discord: "Configure your info" ボタンクリック
    Discord->>InteractionRouter: handleButton()
    InteractionRouter->>UserService: getUser()
    UserService->>UserDAO: get()
    UserDAO->>Database: SELECT
    Database-->>UserDAO: User data
    UserDAO-->>UserService: User data
    UserService-->>InteractionRouter: User
    InteractionRouter->>Discord: ユーザー設定モーダル表示

    User->>Discord: 情報入力（username, password, SSH key）
    Discord->>InteractionRouter: handleModal()
    InteractionRouter->>Discord: 確認メッセージ表示

    User->>Discord: "Yes" ボタンクリック
    Discord->>InteractionRouter: handleConfirmButton()
    InteractionRouter->>UserService: updateUser()
    UserService->>ProxmoxClient: createTag()
    ProxmoxClient-->>UserService: Tag作成完了
    UserService->>UserDAO: update()
    UserDAO->>Database: UPDATE
    Database-->>UserDAO: Success
    UserDAO-->>UserService: Success
    UserService-->>InteractionRouter: Success
    InteractionRouter->>Discord: 完了メッセージ表示
```

### 3. VM電源操作フロー

```mermaid
sequenceDiagram
    actor User
    participant Discord
    participant InteractionRouter
    participant VMService
    participant ProxmoxVMAdapter
    participant ProxmoxClient
    participant ProxmoxVE

    User->>Discord: "Show VM info" ボタンクリック
    Discord->>InteractionRouter: handleButton()
    InteractionRouter->>VMService: listUserVMs()
    VMService->>ProxmoxVMAdapter: listVMs()
    ProxmoxVMAdapter->>ProxmoxClient: get(/nodes/.../qemu)
    ProxmoxClient->>ProxmoxVE: API Request
    ProxmoxVE-->>ProxmoxClient: VM list
    ProxmoxClient-->>ProxmoxVMAdapter: VM list
    ProxmoxVMAdapter-->>VMService: VM[]
    VMService-->>InteractionRouter: VM[]
    InteractionRouter->>Discord: VM選択メニュー表示

    User->>Discord: VM選択
    Discord->>InteractionRouter: handleSelectMenu()
    InteractionRouter->>Discord: VM情報と電源ボタン表示

    User->>Discord: 電源ボタンクリック（例: "Start"）
    Discord->>InteractionRouter: handlePowerControl()
    InteractionRouter->>VMService: powerOn()
    VMService->>ProxmoxVMAdapter: startVM()
    ProxmoxVMAdapter->>ProxmoxClient: post(/nodes/.../qemu/.../status/start)
    ProxmoxClient->>ProxmoxVE: API Request
    ProxmoxVE-->>ProxmoxClient: Success
    ProxmoxClient-->>ProxmoxVMAdapter: Success
    ProxmoxVMAdapter-->>VMService: Success
    VMService-->>InteractionRouter: Success
    InteractionRouter->>Discord: 成功メッセージ表示
```

## ディレクトリ構造

```
app/
├── src/
│   ├── bot/                     # Application Layer
│   │   ├── TerrakkoBot.ts       # メインBotクラス
│   │   └── InteractionRouter.ts # Interactionルーティング
│   ├── commands/                # Command handlers
│   │   └── MenuCommand.ts       # メニューコマンド
│   ├── domain/                  # Domain Layer
│   │   ├── session/
│   │   │   ├── Session.ts       # セッションエンティティ
│   │   │   └── SessionManager.ts # セッション管理
│   │   ├── user/
│   │   │   ├── User.ts          # ユーザーエンティティ
│   │   │   └── UserService.ts   # ユーザービジネスロジック
│   │   └── vm/
│   │       ├── VM.ts            # VMエンティティ
│   │       ├── VMService.ts     # VMビジネスロジック
│   │       └── VMRepository.ts  # VMリポジトリインターフェース
│   ├── infrastructure/          # Infrastructure Layer
│   │   ├── config/
│   │   │   └── Config.ts        # 環境変数管理
│   │   ├── db/
│   │   │   ├── Database.ts      # SQLiteデータベース管理
│   │   │   └── UserDAO.ts       # ユーザーデータアクセス
│   │   └── proxmox/
│   │       ├── ProxmoxClient.ts # Proxmox APIクライアント
│   │       └── ProxmoxVMAdapter.ts # VM操作アダプター
│   ├── types/                   # 型定義
│   │   ├── InteractionContext.ts
│   │   ├── Region.ts
│   │   └── VMStatus.ts
│   ├── ui/                      # Presentation Layer
│   │   ├── ComponentFactory.ts  # UIコンポーネント生成
│   │   ├── EmbedBuilder.ts      # Embed生成
│   │   └── MenuBuilder.ts       # メニュー生成
│   ├── utils/                   # Utilities
│   │   ├── Logger.ts            # ロギング
│   │   ├── Time.ts              # 時間ユーティリティ
│   │   └── Validator.ts         # バリデーション
│   └── index.ts                 # エントリーポイント
├── jest.config.js               # Jest設定
├── jest.setup.js                # Jestセットアップ
├── package.json                 # NPM設定
├── tsconfig.json                # TypeScript設定
├── .env.test                    # テスト環境変数
└── db/                          # SQLiteデータベース
    └── userdata.db
```

## 主要コンポーネントの責務

### Application Layer

#### TerrakkoBot
- Discord Clientの初期化と管理
- Discord イベント（ready, messageCreate, interactionCreate）の処理
- 各種サービスの初期化と依存性注入
- グレースフルシャットダウンの実装

#### InteractionRouter
- Discord Interactionの種類判定とルーティング
- Button、Modal、SelectMenu の各Interactionハンドラー
- セッション管理を使った状態管理
- VM操作と確認フローの実装

#### MenuCommand
- テキストコマンド（`trk!`）の処理
- メインメニューの表示
- ユーザー存在確認と自動登録

### Domain Layer

#### VMService
- VM作成・削除のビジネスロジック
- VM一覧取得とフィルタリング
- VM電源操作（起動、停止、再起動、シャットダウン）
- VM名の重複チェック

#### UserService
- ユーザー登録・更新
- Proxmox Tag IDの生成と作成
- ユーザー情報の取得と検証
- デフォルトユーザーの自動作成

#### SessionManager
- セッションの作成・取得・削除
- セッションタイムアウト管理
- ユーザーごとの最新セッション取得

### Infrastructure Layer

#### ProxmoxClient
- Proxmox VE APIへのHTTPリクエスト
- Token認証の管理
- リージョンとテンプレートIDの管理
- エラーハンドリングとログ記録

#### ProxmoxVMAdapter
- VMのクローン作成
- VM情報の取得
- VM操作（電源管理）の実装
- 次に利用可能なVMIDの取得

#### DatabaseManager & UserDAO
- SQLiteデータベースの初期化
- ユーザーデータのCRUD操作
- トランザクション管理

### Presentation Layer

#### ComponentFactory
- Discord UIコンポーネント（Button、SelectMenu、Modal）の生成
- 動的なコンポーネント生成（VM数、VM選択など）

#### EmbedBuilder
- Discord Embedの生成
- エラー、成功、VM情報のEmbed

#### MenuBuilder
- メインメニューの構築
- VM情報メニューの構築

### Utilities

#### Validator
- VMID、SSH公開鍵、CPU、メモリ、VM数のバリデーション
- 文字列の空チェック

#### Logger
- 構造化ログ出力
- エラーログとスタックトレース記録

#### Config
- 環境変数の読み込みと検証
- JSON形式の環境変数パース

## 設計パターン

### 1. レイヤードアーキテクチャ
各レイヤーが明確に分離され、依存関係は上位レイヤーから下位レイヤーへの一方向のみです。

### 2. Repository パターン
`ProxmoxVMAdapter`が`VMRepository`インターフェースを実装し、データアクセスをカプセル化しています。

### 3. Service パターン
`VMService`と`UserService`がビジネスロジックをカプセル化し、ドメイン層の中心となっています。

### 4. Factory パターン
`ComponentFactory`、`MenuBuilder`、`EmbedBuilder`がUIコンポーネントの生成を担当しています。

### 5. Singleton パターン
`DatabaseManager`がシングルトンパターンを使用してデータベース接続を管理しています。

### 6. Adapter パターン
`ProxmoxVMAdapter`がProxmox APIを内部のVMドメインモデルに変換しています。

## セキュリティ考慮事項

1. **環境変数の管理**: 機密情報（Token、パスワード）は環境変数で管理
2. **入力バリデーション**: すべてのユーザー入力をValidatorクラスで検証
3. **権限チェック**: VM操作時にオーナー確認を実施
4. **HTTPS通信**: Proxmox APIとの通信はHTTPS（証明書検証は無効化）
5. **SQLインジェクション対策**: better-sqlite3のパラメータバインディングを使用
6. **セッション管理**: タイムアウト機能付きセッション管理

## テスト戦略

- **単体テスト**: Jestを使用したユーティリティクラスのテスト
- **統合テスト**: サービス層のテスト（Configとの連携）
- **環境分離**: `.env.test`を使用したテスト専用環境

テストカバレッジ目標:
- Utilities: 100%
- Domain Layer: 80%以上
- Infrastructure Layer: 70%以上

## 今後の拡張性

1. **マルチリージョン対応の強化**: リージョン選択機能の追加
2. **VM監視機能**: VM使用状況のモニタリング
3. **権限管理**: ロールベースアクセス制御（RBAC）
4. **VM テンプレートカスタマイズ**: ユーザーごとのテンプレート選択
5. **通知機能**: VM状態変化の自動通知
6. **スケジューリング**: VM自動起動・停止のスケジュール設定
