# Copilot Instructions for Terrakko

## 言語運用ルール

- ユーザー向けの回答、コードコメント、コミットメッセージ、Issue/PR コメントは原則 **日本語** で記述する。
- 調査時の検索キーワードやブレインストーミングは **英語** を使ってよい。
- Claude 系の運用知見が必要な依頼では、`claude-dotfiles` スキルの方針（`~/.claude/` の安全な同期、機微情報除外）を参照して進める。

## Build / Test / Lint コマンド

このリポジトリは Python Bot を Docker で動かす構成。テスト・lint 専用ツールは現状定義されていない。

```bash
# 起動（推奨）
cd app
docker compose up -d --build

# ログ確認
cd app
docker compose logs -f terrakko

# 停止
cd app
docker compose down
```

```bash
# ローカル実行（.env 設定済み前提）
cd app/src
python terrakko.py
```

```bash
# 最低限の構文確認
python -m py_compile app/src/*.py
```

- **単体テスト実行コマンド**: 未整備（テストスイートなし）
- **lint コマンド**: 未整備

## 高レベルアーキテクチャ

Terrakko は「Discord UI 操作 -> Bot -> Proxmox API」の経路で VM を操作する。

1. `app/src/terrakko.py`
   - Discord Bot のエントリポイント。
   - スラッシュコマンド（`/terrakko vm *`, `/terrakko lxc *`）を `app_commands.Group` の 2 段ネストで実装。
   - build に必要な入力はスラッシュコマンド引数で受け取る。削除時は `DeleteConfirmView`（`View`）で二重確認を行う。
   - `/terrakko console` で DM セッションを開始し、`active_sessions` に登録する。他コマンドはセッション未登録時に拒否する。
2. `app/src/proxmox_ve.py`
   - Proxmox API ラッパー。
   - モジュール import 時に `InitializePVEInfo()` を実行し、`pve` を初期化。
   - `GetRegion()` で全ノードをスキャンし、テンプレートが存在かつ稼働 VM 数最小のノードを動的に選択する。
   - VM 作成・起動・停止・削除・IP 取得を提供。
3. `app/src/config.py`
   - `.env` をロードして設定を集約。
   - `PVE_TEMP_NAME` でテンプレート VM 名を指定。ノード選択は起動時ではなく VM 作成ごとに `GetRegion()` で行う。

補足:

- `app/.env.temp` の `WORKDIR="src"` を `app/docker-compose.yaml` と `app/Dockerfile` が前提にしており、実行作業ディレクトリは `/home/src` になる。
- CI は `.github/workflows/publish.yaml` で GHCR へ Docker イメージを publish する（`main` push / `v*` tag）。

## このコードベース固有の重要な規約

1. **VM 所有権の識別は PVE タグ**
   - `GetNodeVM(author_id)` は `discord_<author_id>` タグを持つ VM を所有 VM として抽出する。
   - VM 作成直後のクローン完了後にタグを付与する（`CreateInstance` 内）。
   - タグ形式（`discord_<discord_user_id>`）を変えると所有権管理が機能しなくなる。

2. **Proxmox ノードとテンプレートは VM 作成ごとに動的選択**
   - `GetRegion()` が全ノードをスキャンし `PVE_TEMP_NAME` に一致するテンプレートを持つノードの中から稼働 VM 数最小のものを選ぶ。
   - `InitializePVEInfo()` は PVE 接続のみ初期化し、ノード・テンプレート選択はしない。

3. **VM ID ガードの範囲を前提に実装**
   - Proxmox 操作関数は `100 <= vmid < 90000` を有効範囲として扱う。
   - 新しい処理追加時も同じ範囲前提で整合させる。

4. **Discord 応答は Ephemeral 中心**
   - UI 操作系のレスポンスは `ephemeral=True` を基本とする。
   - 長時間処理は `WatchTask()` と `monitor_and_notify*` による followup 通知の流れを踏襲する。

5. **設定参照は `config.py` 経由で統一**
   - `os.getenv()` を各モジュールで直接増やすより、`config.py` に追加して import する形が既存パターン。

6. **SSL 検証の既定動作**
   - `PVE_CA_CERT` が空なら system CA を使い、値があればその証明書パスを使う。
   - Proxmox 接続設定変更時はこの分岐を維持する。

## 既存ドキュメントとの対応

- セットアップ詳細: `setup.md`
- 利用フロー（ユーザー向け）: `usage.md`
- 環境変数の雛形: `app/.env.temp`
- 全体概要の補助: `README.md`

実装とドキュメントに差分がある場合は、**現在のコード（`app/src/*.py`）を優先**して判断する。
