# Refactoring Guide: Terrakko Next-Gen (Updated Structure)

## 1. Phase 1: Resource Cleanup & Prep
- [ ] `app/src/db.py` の削除
- [ ] 既存 SQLite DB ファイルの削除
- [ ] `requirements.txt` の更新
- [ ] `terrakko.py` からの DB 関連コードの削除

## 2. Phase 2: Core Refactoring (Async & Tags)
- [ ] `proxmox_ve.py` の非同期化
- [ ] `Tasks.blocking_status` の廃止と監視ループ実装
- [ ] `discord_[uuid]` タグによるフィルタリング実装
- [ ] リージョン問題（動的ノード選択）の修正
- [ ] SSL 検証の有効化
- [ ] 監査ログの実装

## 3. Phase 3: Migration Script
- [ ] `migrate_tags.py` の作成と実施

## 4. Phase 4: Slash Command Interface
- [ ] `/terrakko login` 実装
- [ ] `/terrakko vm start` 実装 (Autocomplete)
- [ ] `/terrakko vm stop` 実装
- [ ] `/terrakko vm status` 実装
- [ ] `/terrakko vm build` 実装 (Modal, Replica)
- [ ] `/terrakko vm delete` 実装 (Double Confirmation)
- [ ] DM 送信失敗時のフォールバック処理

## 5. Phase 5: Security & Deployment
- [ ] Dockerfile の非 root 化
- [ ] 秘密情報保持の最終チェック
