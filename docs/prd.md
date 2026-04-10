# Unified PRD: /terrakko Command Set

## 1. Overview
全機能を `/terrakko` コマンドに統合。リソースごとにサブコマンドグループ（例: `vm`）を設け、将来の拡張性を確保する。

## 2. Command Specifications

### 2.1. /terrakko login (Public Only)
- **Role:** セッション開始。DM へ操作メニューを送信。

### 2.2. /terrakko vm build [name] [template] (DM Only)
- **Role:** テンプレートからのクローン作成。
- **Parameters:** Replica Count, CPU Cores, Memory (MB), Disk Size (GB).
- **Security:** User, Password, SSH-Key (Modal Input).

### 2.3. /terrakko vm start [vmid] (DM Only)
- **Role:** 電源オン。
- **Autocomplete:** 自分のタグがついた VM のみ。

### 2.4. /terrakko vm stop [vmid] (DM Only)
- **Role:** 電源オフ。

### 2.5. /terrakko vm status [vmid] (DM Only)
- **Role:** 詳細ステータス表示。

### 2.6. /terrakko vm delete [vmid] (DM Only)
- **Role:** VM 削除（二重確認必須）。

## 3. Audit Logging
- **Format:** `[TIMESTAMP] [USER_ID] [CMD] [VM_ID] [STATUS/UPID]`

## 4. Constraints & Timeouts
- **Monitoring Timeout:** 15 分。
- **Inactivity Timeout:** 15 分。
