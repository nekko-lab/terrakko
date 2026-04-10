# Architecture Decisions: Next-Generation Terrakko (Updated Command Structure)

## 1. Unified Namespace & Session Flow
### Decision
すべての操作を `/terrakko` トップレベルコマンドの下に集約し、サブコマンドグループでリソースを分類する。

### Implementation Details
- **Root Command:** `/terrakko`
- **Subcommands:**
    - `/terrakko login`: セッション開始（公開チャンネル -> DM）
    - `/terrakko vm <build|start|stop|status|delete>`: VM 操作（DM 専用）
- **Session Flow:** 
    1. 公開チャンネルで `/terrakko login` を実行。
    2. Bot が認証を行い、ユーザーの DM へセッション開始メッセージを送信。
    3. 以降、ユーザーは DM 内で `/terrakko vm start` 等の操作を行う。
    4. **Inactivity Timeout:** 15 分間操作がない場合、セッションを自動終了。

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
