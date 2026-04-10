# Unified PRD: /vm Command Set

## 1. Overview
全機能を `/vm` サブコマンドに集約する。ログイン・セッション管理は行わず、Discord アカウントをそのまま identity として扱うステートレス設計とする。

## 2. Command Specifications

### 2.1. /vm build [name] [template]
- **Role:** テンプレートからのクローン作成。
- **Parameters (Modal Input):** VM 名、レプリカ数、CPU コア数、メモリ (MB)、ディスクサイズ (GB)、CI ユーザー名、パスワード、SSH 公開鍵。
- **Security:** パスワードは一時変数としてのみ保持し、API 呼び出し後に破棄する。
- **Tag:** クローン完了直後に `discord_[uuid]` タグを自動付与する。
- **Response:**
    - **Ephemeral:** 「VM のビルドを開始しました。完了したら DM でお知らせします。」
    - **DM (完了時):** 「VM [name] のビルドが完了しました。IP: [addr]」
    - **DM (失敗時):** 「VM [name] のビルドに失敗しました。」

### 2.2. /vm start [vmid]
- **Role:** VM の起動。
- **Autocomplete:** `discord_[uuid]` タグを持つ、status=stopped の VM のみ候補表示。
- **Response:**
    - **Ephemeral:** 「VM [vmid] の起動を開始しました。完了したら DM でお知らせします。」
    - **DM (完了時):** 「VM [vmid] が起動しました。」
    - **DM (失敗時):** 「VM [vmid] の起動に失敗しました。」

### 2.3. /vm stop [vmid]
- **Role:** VM の停止（シャットダウン）。
- **Autocomplete:** `discord_[uuid]` タグを持つ、status=running の VM のみ候補表示。
- **Response:**
    - **Ephemeral:** 「VM [vmid] の停止を開始しました。完了したら DM でお知らせします。」
    - **DM (完了時):** 「VM [vmid] が停止しました。」

### 2.4. /vm status [vmid]
- **Role:** VM の詳細ステータス表示。
- **Autocomplete:** `discord_[uuid]` タグを持つ全 VM。
- **Response:**
    - **Ephemeral:** VM 名、VMID、リージョン、ステータス、IP アドレスを表示。

### 2.5. /vm delete [vmid]
- **Role:** VM 削除（二重確認必須）。
- **Autocomplete:** `discord_[uuid]` タグを持つ全 VM。
- **Flow:**
    1. 削除対象の VM 情報と「削除を確定する」ボタンを Ephemeral で表示。
    2. ボタン押下時に PVE から最新タグを再取得し、所有権を再確認。
    3. 確認後に削除 API を実行。
- **Response:**
    - **Ephemeral:** 「削除を確定する」ボタン付き確認メッセージ。
    - **DM (完了時):** 「VM [vmid] を削除しました。」

## 3. Error Handling

| ケース | レスポンス |
|--------|-----------|
| VM ID 不正・所有権なし | 「指定された VM は見つかりません（または操作権限がありません）。」|
| すでに起動/停止中 | 「VM [vmid] はすでに [status] 状態です。」|
| PVE API エラー | 「Proxmox サーバーとの通信に失敗しました。時間をおいて再度お試しください。」|
| 操作タイムアウト (15分) | 「操作がタイムアウトしました。/vm status で現在の状態を確認してください。」|
| DM 送信失敗 | Ephemeral メッセージで代替通知。|

## 4. Audit Logging
- **対象操作:** `/vm build`, `/vm delete`
- **Format:** `[TIMESTAMP] [DISCORD_USER_ID] [CMD] [VM_NAME/VM_ID] [STATUS/UPID]`

## 5. Constraints
- **Monitoring Timeout:** 15 分（非同期タスク監視の上限）。
- **No Wildcards:** 一括削除コマンドは実装しない。常に単一の VM ID 指定を必須とする。
