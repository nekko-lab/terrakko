# Terrakko コードベース概要 (v0.2.0)

> 調査日: 2026-04-05  
> 対象ブランチ: v0.4

---

## プロジェクト概要

Terrakko は **Discord Bot 経由で Proxmox VE の VM インスタンスをプロビジョニング**するツール。  
ユーザーは Discord 上のボタン・セレクトメニュー・モーダルといった UI を操作するだけで VM の作成・削除・電源操作・情報確認ができる。

- 言語: Python 3.11
- 実行環境: Docker (python:3.11-slim ベース)
- 外部依存: Proxmox VE API、Discord Bot Token

---

## ディレクトリ構成

```
terrakko/
├── app/
│   ├── src/
│   │   ├── terrakko.py       # エントリポイント・Discord Bot 本体
│   │   ├── proxmox_ve.py     # Proxmox VE API ラッパー
│   │   ├── config.py         # 設定・環境変数ロード
│   │   ├── db.py             # SQLite CRUD (aiosqlite)
│   │   └── db/
│   │       └── userdata.db.deny  # DB ファイル除外設定
│   ├── db/
│   │   └── userdata.db       # SQLite 実データ (コンテナ内 ./db/ にマウント)
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   ├── requirements.txt
│   ├── terrakko.yaml         # Kubernetes Deployment マニフェスト (参考用)
│   └── .env                  # 秘密情報 (git 管理外)
├── docs/                     # ← このドキュメントが置かれる場所
├── images/                   # スクリーンショット・フローチャート
├── releasenotes/
│   └── releasenote-20250222.md
├── README.md
├── setup.md
├── usage.md
└── config.md
```

---

## 各ファイルの役割

### `src/config.py`

環境変数をロードして定数として公開する設定モジュール。

| 変数 | 内容 |
|------|------|
| `version` | `"0.2.0"` |
| `DOMAIN` | VM のホスト名サフィックス (例: `.nekko.cloud`) |
| `TIME` | UI タイムアウト秒数 (180秒) |
| `db_path` / `dbname` / `usrdata` | SQLite ファイルパス (`./db/userdata.db`) |
| `PVE_HOST/USER/PASS/TOKEN/SECRET` | Proxmox VE 接続情報 |
| `PVE_REGION` | ノード名リスト (JSON配列) |
| `PVE_TEMP_ID` | テンプレート VM ID リスト (JSON配列、Region と 1:1 対応) |
| `DIS_TOKEN` | Discord Bot トークン |
| `DIS_CHANNEL_ID` | 対象チャンネル ID |

`PVE_REGION` と `PVE_TEMP_ID` は **インデックスで対応**する設計になっており、ランダムに選択されたリージョン番号が両方に使われる。

---

### `src/db.py`

aiosqlite を使った非同期 SQLite ラッパー。

**テーブル: `userdata`**

| カラム | 型 | 内容 |
|--------|----|------|
| `id` | INTEGER PK | 自動採番 |
| `uuid` | STRING | Discord ユーザー ID |
| `username` | STRING | Cloud-init ユーザー名 |
| `password` | STRING | Cloud-init パスワード (平文保存) |
| `sshkey` | STRING | SSH 公開鍵 |

**公開関数**

| 関数 | 説明 |
|------|------|
| `create_table()` | テーブルを初期化 (モジュールロード時に自動実行) |
| `insert_data(userid, username, password, sshkey)` | 新規ユーザー登録 |
| `update_data(userid, username, password, sshkey)` | ユーザー情報更新 |
| `get_userdata(userid)` | Discord ID でユーザー情報を 1 件取得 |
| `get_column(column)` | 指定カラムの全行を取得 |
| `delete_database()` | DB ファイルを削除 |

**既知の問題**
- パスワードが平文で SQLite に保存されている。`bcrypt` が requirements.txt に含まれているが未使用。

---

### `src/proxmox_ve.py`

ProxmoxAPI を使った VM 操作ラッパー。モジュールロード時に `InitializePVEInfo()` を自動実行する。

**グローバル変数** (初期化後に利用可)

| 変数 | 内容 |
|------|------|
| `pve` | `ProxmoxAPI` インスタンス |
| `region` | ランダムに選択されたノード名 |
| `node` | `pve.nodes(region)` のショートカット |
| `temp_id` | 選択されたリージョンに対応するテンプレート VM ID |

**公開関数**

| 関数 | 説明 |
|------|------|
| `InitializePVEInfo()` | PVE 接続・リージョン選択・テンプレート ID 取得 |
| `GetVMID()` | PVE クラスタから次の利用可能な VM ID を取得 |
| `GetNodeVM(author_id)` | 全ノードから `{author_id}-*` にマッチする VM 一覧を取得 |
| `GetVMStatus(r, vmid)` | 指定 VM のステータスを取得 |
| `GetVMIPAddresses(r, vmid)` | QEMU Guest Agent 経由で IPv4/IPv6 を取得 |
| `CreateInstance(clone_vm_id, vm_name, ciuser, passwd, sshkey)` | テンプレートをクローンし Cloud-init で初期化・起動 |
| `InitializeInstance(vmid, ciuser, passwd, sshkey)` | Cloud-init 設定を適用して VM を起動 |
| `StartInstance(r, vmid)` | VM を起動 |
| `StopInstance(r, vmid)` | VM を強制停止 |
| `ShutdownInstance(r, vmid)` | VM をシャットダウン |
| `RebootInstance(r, vmid)` | VM を再起動 |
| `DeleteInstance(r, vmid)` | VM を削除 (停止済みのみ) |

**VM ID の有効範囲**: `100 <= vmid < 90000`

**リージョン選択の仕組み**  
起動時に `PVE_REGION` からランダムに 1 つ選ぶ。選択後は再起動するまで固定される。複数ノードへの負荷分散として機能するが、**起動後に変更できない**。

---

### `src/terrakko.py`

Discord Bot 本体。discord.py の `commands.Bot` を使用。  
コマンドプレフィックスは `trk` またはメンション。

#### UI 画面遷移

```
trk! コマンド
  └─ StartButton (緑: Start)
       └─ MainMenu
            ├─ [Create VM] → SelectVMNumberTab (1〜5台選択)
            │                  └─ ProfileConfigurationForm (Modal: VM名入力)
            │                       └─ ConfirmAndExecute (Yes/No)
            │                            └─ proxmox_ve.CreateInstance()
            │
            ├─ [Show VM info] → SelectVMNameTab (mode=info)
            │                     └─ OperateVMPower (Start/Shutdown/Reboot/Stop)
            │
            ├─ [Delete VM] → SelectVMNameTab (mode=delete)
            │                  └─ ConfirmAndExecute (Yes/No)
            │                       └─ proxmox_ve.DeleteInstance()
            │
            └─ [Configure your info] → SetUserInfoForm (Modal: username/password/sshkey)
                                          └─ ConfirmAndExecute (Yes/No)
                                               └─ db.update_data()
```

#### クラス・関数一覧

| クラス / 関数 | 種別 | 説明 |
|---------------|------|------|
| `UserSession` | クラス | Discord コンテキストからユーザー ID を取得するユーティリティ |
| `WaitForTaskCompletion()` | 関数 | タスク完了をポーリング待機する (未完成: 後述) |
| `StartButton` | View | メニュー起動ボタン |
| `MainMenu` | View | Create VM / Show VM info / Delete VM / Configure your info の 4 ボタン |
| `SelectVMNumberTab` | View | 作成台数 1〜5 のセレクトメニュー |
| `ProfileConfigurationForm` | Modal | VM 名入力フォーム |
| `SelectVMNameTab` | View | VM 一覧セレクト (delete / info モード共用) |
| `OperateVMPower` | View | Start / Shutdown / Reboot / Stop ボタン |
| `ConfirmAndExecute` | View | Yes / No 確認ボタン (create / delete / userdata モード共用) |
| `SetUserInfoForm` | Modal | username / password / sshkey 編集フォーム |
| `DeleteDB` | View | DB 削除確認ボタン (現在無効化) |
| `ShowMenu()` | コマンド (`trk!`) | メインエントリ |
| `delete_db()` | コマンド (`trkdelete_db`) | DB 削除コマンド (現在無効化) |

---

## インフラ・実行環境

### Dockerfile

- ベース: `python:3.11-slim`
- `gcc` / `libsqlite3-dev` をインストール後、`requirements.txt` で Python ライブラリをインストール
- コンテナ起動時に `python terrakko.py` を実行
- `./db/` ディレクトリをコンテナ内に作成

### docker-compose.yaml

- `${WORKDIR}` 環境変数でワーキングディレクトリを指定
- `.env` ファイルを環境変数として注入
- タイムゾーン: Asia/Tokyo

### terrakko.yaml (Kubernetes)

`discord-dogbot` という名前の Deployment マニフェストが存在するが、**Terrakko 本体ではなく別サービス**の設定ファイルが誤って混入している可能性がある。

---

## 既知の問題・技術的負債

| # | 箇所 | 内容 |
|---|------|------|
| 1 | `db.py:43` | パスワードが平文保存。`bcrypt` が入っているのに未使用 |
| 2 | `terrakko.py:109` | VM 作成後に `asyncio.sleep(180)` で固定待機。cloud-init 完了を検知する仕組みがなく、コメントでも「変更したい」と明記されている |
| 3 | `terrakko.py:148` | `WaitForTaskCompletion` のループ条件が `while data["status"] == vm_status` となっており、初期値 `""` と期待値が一致しないため**即時終了**する。ポーリングとして機能していない |
| 4 | `terrakko.py:155` | `print({vmid} is data["status"])` — `{vmid}` が `set` リテラルになっており構文エラーではないが意図通りに動かない |
| 5 | `terrakko.py:1116,1119,1143,1148` | `DeleteDB` の `interaction.response.send_message()` が `await` なしで呼ばれている (コルーチンが実行されない) |
| 6 | `proxmox_ve.py:75-82` | 起動時にリージョンをランダム選択し、以降は固定。再起動しないと別リージョンに切り替わらない |
| 7 | `terrakko.py:1059` | `get_column("uuid")` の返値が `[(id,), ...]` 形式なのに `row[0]` で比較しているため、Discord ID (`int`) と DB の uuid (`STRING`) の型不一致が起こる可能性がある |
| 8 | `config.py:65` | `DIS_CHANNEL_ID` を取得しているが、Bot 本体では使用されていない |

---

## 依存ライブラリ

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| `discord.py` | 2.4.0 | Discord Bot フレームワーク |
| `proxmoxer` | 2.1.0 | Proxmox VE REST API クライアント |
| `aiosqlite` | 0.20.0 | 非同期 SQLite |
| `bcrypt` | 4.2.0 | パスワードハッシュ (未使用) |
| `python-dotenv` | 1.0.1 | `.env` ファイル読み込み |
| `requests` | 2.32.3 | HTTP クライアント (proxmoxer の依存) |
| `urllib3` | 2.2.3 | HTTP クライアント |
| `asyncio` | 3.4.3 | 非同期処理 |
| `pysqlite3` | 0.5.4 | SQLite バインディング |

---

## v0.5 に向けた改善候補

調査を通じて見えた、次バージョンで対応すべき主な課題：

1. **cloud-init 完了検知** — 固定 180秒 sleep から、QEMU Agent 経由の完了ポーリングへ変更
2. **パスワードの bcrypt ハッシュ化** — `db.py` の insert/update 時に `bcrypt.hashpw()` を適用
3. **`WaitForTaskCompletion` のバグ修正** — ポーリングループが即時終了する問題を修正
4. **リージョン選択の改善** — コマンド実行ごとに選択するか、ラウンドロビン方式への変更
5. **`terrakko.yaml` の整理** — 別サービスのマニフェストの整理または削除
