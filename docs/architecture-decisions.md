# Architecture Decisions: Next-Generation Terrakko (Updated Command Structure)

## 1. Unified Namespace & Stateless Command Flow
### Decision
すべての操作を `/vm` サブコマンドに集約する。ログイン・セッション管理は実装しない。

### Implementation Details
- **Subcommands:** `/vm <build|start|stop|delete>`
- **Flow:** スラッシュコマンドを直接実行。完了通知は DM で行う（DM Fallback は §3 参照）。
- **No Session:** セッション状態をBotが保持しない完全ステートレス設計。

## 2. No Login / Stateless Identity Model
### Decision
`/vm login` コマンドおよびセッション管理機能は実装しない。Discord アカウントの認証をそのまま identity として信頼する。

### Rationale
- Keycloak ↔ PVE の認証連携は、管理者が PVE コンソールに直接アクセスするための仕組みであり、Botのユースケースとは責務が異なる。
- Bot は単一の PVE サービスアカウント（`PVE_TOKEN`）で動作する特権エージェントとして位置づける。
- Discord の OAuth2 認証によって「誰がコマンドを発行したか」は既に保証されており、追加のログインは二重管理になる。

### Known Limitation
Discord UUID と Keycloak / PVE の個人アカウントは紐づいていないため、「PVE レベルで誰が VM を作成したか」の特定は困難。この制約は意図的に許容する。将来 Keycloak との OAuth2 連携が必要になった場合は OIDC フローの導入を検討すること。

### Boundary
- Botのロジック内では `discord_[uuid]` タグによる所有権確認を必須とし、他ユーザーの VM への操作を防ぐ。
- PVE サービスアカウントが漏洩した場合、Bot のロジックによる保護は無効になる点はインフラレベルの管理で対処する。

## 2. Asynchronous Task Management & Monitoring
### Decision
`asyncio` による非同期監視。タイムアウト値 15 分。

## 3. DM Fallback Strategy
### Decision
DM 送信失敗時は公開チャンネルに Ephemeral メッセージで警告。

## 4. Resource Mapping & Tagging (Zero-DB)
### Decision
`discord_[uuid]` タグによる所有権管理。
- **Tagging Timing:** `clone` 成功直後、`cloud-init` 設定前に付与。
