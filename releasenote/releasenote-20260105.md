# Terrakko v0.4.0 Release Note

**リリース日**: 2026年1月5日

---

## 概要

Terrakko v0.4.0は、**Discord.py から Discord.js への完全なフルリプレイス**を実施した大規模なリファクタリングリリースです。PythonベースのアーキテクチャからTypeScript/Node.jsベースへ全面的に移行し、よりモダンで保守性の高いコードベースへと刷新しました。

---

## 主な変更内容

### 1. Discord.py → Discord.js へのフルリプレイス

#### 技術スタックの刷新
- **言語**: Python → **TypeScript**
- **ランタイム**: Python 3.x → **Node.js 18+**
- **Discordライブラリ**: Discord.py → **Discord.js v14**
- **データベースライブラリ**: sqlite3 → **better-sqlite3**
- **HTTPクライアント**: aiohttp → **Axios**

#### 実装の完全な書き換え
すべてのコンポーネントがTypeScriptで再実装されました:

| コンポーネント | Discord.py (旧) | Discord.js (新) |
|------------|----------------|----------------|
| Botクラス | `TerrakkoBot` (Python) | `TerrakkoBot` (TypeScript) |
| コマンド処理 | `@bot.command()` デコレータ | メッセージイベントハンドラ |
| Interaction処理 | View/Modalクラス | `InteractionRouter` クラス |
| 非同期処理 | `async/await` (asyncio) | `async/await` (Promise) |
| データベース | sqlite3 (同期) | better-sqlite3 (同期) |

---

### 2. アーキテクチャの改善

#### レイヤードアーキテクチャの導入
明確な責任分離を実現するため、以下の層を導入:

```
Presentation Layer (UI)
    ↓
Application Layer (Bot/Commands)
    ↓
Domain Layer (Business Logic)
    ↓
Infrastructure Layer (External Systems)
    ↓
Utilities Layer
```

#### 主要な設計パターンの適用
- **Repository パターン**: `ProxmoxVMAdapter` による抽象化
- **Service パターン**: `VMService`, `UserService` によるビジネスロジックのカプセル化
- **Factory パターン**: UI コンポーネント生成の統一
- **Singleton パターン**: `DatabaseManager` による接続管理
- **Adapter パターン**: Proxmox API の内部モデルへの変換

---

### 3. 新機能

#### テスト環境の追加
- **Jest + ts-jest** による単体テスト環境の構築
- `.env.test` ファイルを使用したテスト専用環境変数の分離
- 現在34個のテストが実装され、すべてパス

#### セッション管理の強化
- `SessionManager` クラスによる状態管理
- タイムアウト機能（デフォルト180秒）
- ユーザーごとの最新セッション取得機能

#### Proxmox Tag機能の追加
- Discord ユーザー名ベースの Tag ID 自動生成
- VM作成時に自動的にユーザータグを付与
- タグによるVM所有者の明確化

---

### 4. コード品質の向上

#### TypeScript による型安全性
- すべてのクラス、関数、変数に型定義を追加
- インターフェースと型エイリアスによる契約の明確化
- コンパイル時の型チェックによるバグの早期発見

#### モジュール化とコード整理
旧実装の課題:
- 単一ファイルに多くのロジックが集中
- 責任の分離が不明確
- テストが困難

新実装の改善:
- 機能ごとにファイルを分割（24ファイル）
- 各クラスの責任を明確化
- テスタビリティの向上

#### エラーハンドリングの統一
- `Logger` クラスによる統一されたログ出力
- エラーメッセージのフォーマット統一（"ERROR" 形式）
- try-catch によるエラーの適切な捕捉と処理

---

### 5. パフォーマンスの改善

#### 非同期処理の最適化
- Discord.js の Promise ベース非同期処理による効率的な実装
- better-sqlite3 による高速なデータベース操作（同期API）
- Axios による HTTP リクエストの最適化

#### データベース接続の改善
- シングルトンパターンによる接続の再利用
- トランザクション処理の適切な実装
- 接続プールの効率的な管理

---

## 移行ガイド

### 環境変数の変更
環境変数のフォーマットに変更はありませんが、以下の点に注意してください:

```bash
# JSON配列形式の環境変数（引用符で囲む）
PVE_REGION=["dev-proxmox-mk", "dev-proxmox-ur"]
PVE_TEMP_ID=["90100", "90101"]
```

### コマンドの変更
**変更なし** - ユーザーインターフェースは完全に互換性があります:
- コマンドトリガー: `trk!` または `@terrakko !`
- 操作フロー: Discord.py版と同一

### データベース互換性
**完全互換** - 既存のSQLiteデータベースをそのまま使用できます。スキーマに変更はありません。

---

## 破壊的変更

### なし
このリリースはフルリプレイスですが、ユーザー体験とデータの互換性は完全に保たれています。

---

## 既知の問題

現時点で既知の問題はありません。

---

## 今後の予定

### v0.5.0 (予定)
- [ ] VM監視機能の追加
- [ ] リージョン選択機能の実装
- [ ] カバレッジ80%以上のテスト追加

### v0.6.0 (予定)
- [ ] ロールベースアクセス制御（RBAC）
- [ ] VM使用状況レポート機能
- [ ] スケジューリング機能（自動起動・停止）

---

## 技術的な詳細

### ファイル構成の変更

#### 旧構成 (Discord.py)
```
src/
├── bot.py                    # すべてのロジックが集中
├── database.py               # DB処理
└── config.py                 # 設定
```

#### 新構成 (Discord.js)
```
app/src/
├── bot/                      # Application Layer
├── commands/                 # コマンドハンドラ
├── domain/                   # ドメインロジック
│   ├── session/
│   ├── user/
│   └── vm/
├── infrastructure/           # インフラ層
│   ├── config/
│   ├── db/
│   └── proxmox/
├── types/                    # 型定義
├── ui/                       # UIコンポーネント
└── utils/                    # ユーティリティ
```

### 依存関係

#### 本番環境
```json
{
  "axios": "^1.7.7",
  "better-sqlite3": "^11.6.0",
  "discord.js": "^14.14.1",
  "dotenv": "^16.4.5"
}
```

#### 開発環境
```json
{
  "@types/better-sqlite3": "^7.6.11",
  "@types/jest": "^30.0.0",
  "@types/node": "^20.19.27",
  "jest": "^30.2.0",
  "ts-jest": "^29.4.6",
  "ts-node": "^10.9.2",
  "typescript": "^5.5.3"
}
```

---

## 貢献者

このリリースにご協力いただいた皆様に感謝します。

---

## サポート

問題が発生した場合は、以下をご確認ください:

1. **ドキュメント**: [usage.md](../usage.md)、[architecture.md](../architecture.md)
2. **テスト実行**: `npm test` でテストが通るか確認
3. **ログ確認**: エラーログを確認し、詳細情報を取得

---

## まとめ

Terrakko v0.4.0は、Discord.pyからDiscord.jsへの完全移行により、以下を実現しました:

✅ **モダンな技術スタック**: TypeScript + Node.js + Discord.js
✅ **優れた設計**: レイヤードアーキテクチャと設計パターンの適用
✅ **高い保守性**: 明確な責任分離とモジュール化
✅ **テスト環境**: Jest による自動テスト
✅ **完全な互換性**: ユーザー体験とデータの互換性を維持

今後もTerrakkoの機能向上と品質改善に取り組んでまいります。

---

**Terrakko Development Team**
2026年1月5日
