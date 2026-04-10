# Implementation & Deployment Plan: Terrakko Next-Gen (Updated Structure)

## 1. Security & Requirements
- `verify_ssl=True` 必須化。
- 秘密情報の永続化排除。

## 2. Phase 1: Resource Cleanup
- `db.py` 廃止、SQLite 削除。
- `requirements.txt` 更新。

## 3. Phase 2: Core Refactoring (Async & Tags)
- `proxmox_ve.py` の非同期化。
- リージョン固定問題の修正。
- 監査ログの実装。

## 4. Phase 3: Migration Script
- `migrate_tags.py` による既存 VM への `discord_[uuid]` 付与。

## 5. Phase 4: Slash Command Interface
- `/terrakko login` の実装。
- `/terrakko vm` サブコマンドグループ（start, stop, status, build, delete）の実装。
- Autocomplete と DM Fallback の実装。
