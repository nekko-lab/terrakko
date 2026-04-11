# Terrakko

<img align="right" src="./logos/terrakko_icon.png" alt="Terrakko logo" width=250cm>

---

## 目次

- [Terrakko](#terrakko)
  - [目次](#目次)
  - [Terrakkoとは？](#terrakkoとは)
  - [事前要件](#事前要件)
  - [使い方](#使い方)
    - [VMを作成する](#vmを作成する)
    - [VMを起動する](#vmを起動する)
    - [VMを停止する](#vmを停止する)
    - [VMのステータスを確認する](#vmのステータスを確認する)
    - [VMを削除する](#vmを削除する)
  - [操作の通知について](#操作の通知について)

## Terrakkoとは？

TerrakkoはDiscordから簡単な操作でNekko CloudのVMインスタンスの作成・起動・停止・削除が行える対話型のコンソールです。  
スラッシュコマンド (`/terrakko`) を使用してVMを操作します。操作の完了はDiscordのDMで通知されます。

## 事前要件

- SSH公開鍵の作成（パスワード認証を使用する場合は不要）

## 使い方

すべてのコマンドはスラッシュコマンド形式です。Discord のメッセージ入力欄に `/terrakko` と入力するとコマンド候補が表示されます。

### VMを作成する

コマンド: `/terrakko vm build`

1. `/terrakko vm build` を実行するとモーダル（入力フォーム）が表示されます。
2. 以下の情報を入力します。

   | 項目 | 内容 |
   | :--- | :--- |
   | VM Name | VM の名前 |
   | Replica Count | 作成する VM の台数（複数台の場合は `name-1`, `name-2` と自動命名）|
   | SSH Public Key | SSH 公開鍵（省略可。省略した場合はパスワード認証のみ有効）|
   | Username | モーダルで入力する Cloud-init ユーザー名 |

   > **Note:** パスワードはサーバー側で自動生成されます（英数字 10 文字）。ビルド完了後の DM に記載されたワンタイムリンク（15分有効）から確認してください。リンクへのアクセスが失敗した場合は PVE WebコンソールのCloud-initから変更してください。

3. 送信後、チャンネルに「ビルドを開始しました」と Ephemeral（自分にのみ表示）メッセージが届きます。
4. ビルド完了後、DM で完了通知とパスワード取得用のワンタイムリンクが届きます。

### VMを起動する

コマンド: `/terrakko vm start [vmid]`

1. `/terrakko vm start` を入力すると、自分が所有する停止中 (stopped) の VM が候補として表示されます。
2. 起動したい VM を選択して実行します。
3. チャンネルに「起動を開始しました」と Ephemeral メッセージが届きます。
4. 起動完了後、DM で完了通知が届きます。

### VMを停止する

コマンド: `/terrakko vm stop [vmid]`

1. `/terrakko vm stop` を入力すると、自分が所有する起動中 (running) の VM が候補として表示されます。
2. 停止したい VM を選択して実行します。
3. チャンネルに「停止を開始しました」と Ephemeral メッセージが届きます。
4. 停止完了後、DM で完了通知が届きます。

> **Note:** `stop` はシャットダウン（グレースフル停止）を行います。

### VMのステータスを確認する

コマンド: `/terrakko vm status [vmid]`

1. `/terrakko vm status` を入力すると、自分が所有する全 VM が候補として表示されます。
2. 確認したい VM を選択して実行します。
3. 以下の情報が Ephemeral メッセージで表示されます（自分にのみ表示）。

   | 項目 | 詳細 |
   | :--- | :--- |
   | VM Name | VM の名前 |
   | VMID | PVE が管理する VM 固有の ID |
   | Region | VM のリージョン |
   | Status | VM の状態 (running / stopped) |
   | Host Name | Service Discovery が提供する VM 固有のドメイン名 |
   | IPv4 / IPv6 | VM の IP アドレス |

### VMを削除する

コマンド: `/terrakko vm delete [vmid]`

> **Warning:** この操作は取り消せません。

1. `/terrakko vm delete` を入力すると、自分が所有する全 VM が候補として表示されます。
2. 削除したい VM を選択して実行します。
3. 削除対象の VM 情報と「削除を確定する」ボタンが Ephemeral メッセージで表示されます。
4. 内容を確認し「削除を確定する」ボタンをクリックします。
5. 削除完了後、DM で完了通知が届きます。

> **Note:** 起動中 (running) の VM は削除できません。先に `/terrakko vm stop` で停止してから削除してください。

## 操作の通知について

- 各コマンドの実行受付は、チャンネルに **Ephemeral メッセージ**（自分にのみ表示）で即時通知されます。
- 非同期処理の完了（またはエラー）は **DM** で通知されます。
- DM の受信が無効になっている場合は、代わりにチャンネルへ Ephemeral メッセージで通知されます。
- 操作の監視タイムアウトは **15 分**です。タイムアウト後は `/terrakko vm status` で現在の状態を確認してください。
