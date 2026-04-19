# Terrakko

<img align="right" src="./logos/terrakko_icon.png" alt="Terrakko logo" width="250">

Terrakko は Discord のスラッシュコマンドから Proxmox VE の VM インスタンスを操作できる ChatOps ツールです。

```text
                                              _  
  _____  _____ ____  ____  ____  _  __ _  __ |_\_  
 /__ __\/  __//  __\/  __\/  _ \/ |/ // |/ //\_  \_  
   / \  |  \  |  \/||  \/|| /_\||   / |   /|_  \_  \  
   | |  |  /_ |    /|    /| | |||   \ |   \| \_  \__|  
   \_/  \____\\_/\_\\_/\_\\_/ \/\_|\_\\_|\_\\__\___/  
```

---

## 機能

| コマンド | 説明 |
| -------- | ---- |
| `/terrakko console` | DM セッションを開始する（VM 操作コマンドの使用前に必須） |
| `/terrakko help` | 利用可能なコマンド一覧を表示 |
| `/terrakko vm build` | テンプレートから VM を作成（Cloud-init 対応） |
| `/terrakko vm list` | 所有する VM の一覧を表示 |
| `/terrakko vm start` | 停止中の VM を起動 |
| `/terrakko vm shutdown` | 起動中の VM をグレースフルシャットダウン（ACPI シグナル） |
| `/terrakko vm stop` | 起動中の VM を強制停止（電源断） |
| `/terrakko vm status` | VM のステータス・IP アドレスを確認 |
| `/terrakko vm delete` | VM を削除（二重確認あり） |
| `/terrakko lxc *` | LXC コンテナ操作（実装予定） |

すべての操作は非同期で実行され、完了時に Discord DM で通知されます。

---

## アーキテクチャ

### ステートレス設計

- セッション管理・ログイン機能はなし。Discord アカウントをそのまま identity として扱う。
- Bot は単一の PVE サービスアカウント（`PVE_TOKEN`）で動作する特権エージェント。
- DB なし。VM の所有権は PVE タグ（`discord_<discord_user_id>`）で管理する。

### タグベース所有権

- VM 作成時にクローン完了直後に `discord_<discord_user_id>` タグを自動付与。
- 各コマンドは自分の Discord ユーザー ID に対応するタグを持つ VM のみ操作対象とする。

### 非同期タスク監視

- コマンド受付後、PVE タスクをバックグラウンドで監視（`asyncio.create_task`）。
- 完了・失敗を DM で通知。DM が無効な場合は Ephemeral メッセージにフォールバック。
- 監視タイムアウト: 15 分。

### 動的ノード選択

- 利用可能な全ノードを API で自動検出（`PVE_REGION` の手動設定不要）。
- `PVE_TEMP_NAME` で指定したテンプレートが存在するノードのみ候補とし、稼働 VM 数が最も少ないノードを選択。

---

## Requirements

### 実行環境

- Docker (python:3.14-slim ベース)

### Proxmox VE 権限（TerrakkoAccess ロール）

| 権限 | 用途 |
| ---- | ---- |
| `VM.Clone` | テンプレートから VM をクローン |
| `VM.Monitor` | QEMU Guest Agent 経由で IP アドレス取得 |
| `VM.PowerMgmt` | VM の起動・停止 |
| `VM.Audit` | VM 一覧・ステータス取得 |
| `VM.Allocate` | 新規 VM へのリソース割り当て |
| `VM.Config.Cloudinit` | Cloud-init 設定（ユーザー名・パスワード・SSH キー） |
| `VM.Config.Options` | VM タグ設定（所有権管理） |
| `SDN.Use` | SDN の使用 |
| `Datastore.AllocateSpace` | ストレージ領域の割り当て |

### Python ライブラリ（[`requirements.txt`](app/requirements.txt)）

| パッケージ | バージョン |
| ---------- | ---------- |
| [`discord.py`](https://discordpy.readthedocs.io/ja/latest/) | 2.7.1 |
| [`proxmoxer`](https://proxmoxer.github.io/docs/latest/) | 2.3.0 |
| [`python-dotenv`](https://github.com/theskumar/python-dotenv) | 1.2.2 |
| [`requests`](https://requests.readthedocs.io/en/latest/) | 2.33.1 |
| [`urllib3`](https://urllib3.readthedocs.io/en/stable/) | 2.6.3 |

---

## ドキュメント

- [セットアップ](setup.md)
- [使い方](usage.md)
- [設定リファレンス](config.md)

---

## Contact Us

- <networkcontentslab@gmail.com>
