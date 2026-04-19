# Terrakko

<img align="right" src="./logos/terrakko_icon.png" alt="Terrakko logo" width="250">

---

## 目次

- [Terrakko](#terrakko)
  - [目次](#目次)
  - [Terrakkoとは？](#terrakkoとは)
  - [事前要件](#事前要件)
  - [使い方](#使い方)
    - [DMセッションを開始する](#dmセッションを開始する)
    - [コマンド一覧を表示する](#コマンド一覧を表示する)
    - [VMを作成する](#vmを作成する)
    - [VM一覧を確認する](#vm一覧を確認する)
    - [VMを起動する](#vmを起動する)
    - [VMをシャットダウンする](#vmをシャットダウンする)
    - [VMを強制停止する](#vmを強制停止する)
    - [VMのステータスを確認する](#vmのステータスを確認する)
    - [VMを削除する](#vmを削除する)
  - [操作の通知について](#操作の通知について)

## Terrakkoとは？

TerrakkoはDiscordから簡単な操作でNekko CloudのVMインスタンスの作成・起動・停止・削除が行える対話型のコンソールです。  
スラッシュコマンド (`/terrakko`) を使用してVMを操作します。操作の完了はDiscordのDMで通知されます。

> **重要:** VM 操作コマンドを使用する前に、必ず `/terrakko console` を実行して DM セッションを開始してください。

## 事前要件

- SSH公開鍵の作成（パスワード認証を使用する場合は不要）

## 使い方

すべてのコマンドはスラッシュコマンド形式です。Discord のメッセージ入力欄に `/terrakko` と入力するとコマンド候補が表示されます。

### DMセッションを開始する

コマンド: `/terrakko console`

1. `/terrakko console` を実行すると、Terrakko から DM が送信されます。
2. DM の受信が確認できたら、以降の VM 操作コマンドが使用可能になります。

> **Note:** DM の受信が無効になっている場合は、このサーバーのメンバーからの DM を許可してから再実行してください。

### コマンド一覧を表示する

コマンド: `/terrakko help`

1. `/terrakko help` を実行すると、利用可能なすべてのコマンドと説明が Ephemeral メッセージで表示されます。

### VMを作成する

コマンド: `/terrakko vm build`

1. `/terrakko vm build` を実行し、スラッシュコマンドのオプションとして以下の情報を入力します。

   | 項目 | 必須 | デフォルト | 内容 |
   | :--- | :---: | :---: | :--- |
   | name | ✓ | — | VM の名前 |
   | ciuser | ✓ | — | Cloud-init ユーザー名 |
   | cpu | — | 2 | CPU コア数 |
   | memory | — | 2048 | メモリ容量（MB） |
   | disk | — | 20 | ストレージ容量（GB） |
   | replicas | — | 1 | 作成台数。複数台の場合は `name-1`, `name-2` と自動命名 |
   | sshkey | — | — | SSH 公開鍵（省略時はパスワード認証のみ有効）|

   > **Note:** パスワードはサーバー側で自動生成されます（英数字 10 文字）。ビルド完了後の DM に記載されたワンタイムリンク（15分有効）から確認してください。リンクへのアクセスが失敗した場合は PVE WebコンソールのCloud-initから変更してください。

2. 実行後、チャンネルに「ビルドを開始しました」と Ephemeral（自分にのみ表示）メッセージが届きます。
3. ビルド完了後、DM で完了通知とパスワード取得用のワンタイムリンクが届きます。

### VM一覧を確認する

コマンド: `/terrakko vm list`

1. `/terrakko vm list` を実行すると、自分が所有する全 VM の一覧が Ephemeral メッセージで表示されます。

   | 項目 | 詳細 |
   | :--- | :--- |
   | VM Name | VM の名前 |
   | VMID | PVE が管理する VM 固有の ID |
   | Region | VM のリージョン（ノード名） |
   | Domain | VM に割り当てられたドメイン名 |
   | Status | VM の状態（🟢 running / 🔴 stopped） |

### VMを起動する

コマンド: `/terrakko vm start [vmid]`

1. `/terrakko vm start` を入力すると、自分が所有する停止中 (stopped) の VM が候補として表示されます。
2. 起動したい VM を選択して実行します。
3. チャンネルに「起動を開始しました」と Ephemeral メッセージが届きます。
4. 起動完了後、DM で完了通知が届きます。

### VMをシャットダウンする

コマンド: `/terrakko vm shutdown [vmid]`

1. `/terrakko vm shutdown` を入力すると、自分が所有する起動中 (running) の VM が候補として表示されます。
2. シャットダウンしたい VM を選択して実行します。
3. チャンネルに「シャットダウンを開始しました」と Ephemeral メッセージが届きます。
4. シャットダウン完了後、DM で完了通知が届きます。

> **Note:** `shutdown` は OS に ACPI シグナルを送信してグレースフルにシャットダウンします。通常の停止操作にはこちらを使用してください。

### VMを強制停止する

コマンド: `/terrakko vm stop [vmid]`

1. `/terrakko vm stop` を入力すると、自分が所有する起動中 (running) の VM が候補として表示されます。
2. 強制停止したい VM を選択して実行します。
3. チャンネルに「強制停止を開始しました」と Ephemeral メッセージが届きます。
4. 停止完了後、DM で完了通知が届きます。

> **Warning:** `stop` は電源断（force stop）です。OS のシャットダウン処理を経由しないため、ファイルシステムが破損するリスクがあります。`shutdown` が応答しない場合のみ使用してください。

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

1. `/terrakko vm delete` を入力すると、自分が所有する停止中 (stopped) の VM が候補として表示されます。
2. 削除したい VM を選択して実行します。
3. 削除対象の VM 情報と「削除を確定する」ボタンが Ephemeral メッセージで表示されます。
4. 内容を確認し「削除を確定する」ボタンをクリックします。
5. 削除完了後、DM で完了通知が届きます。

> **Note:** 起動中 (running) の VM は削除できません。先に `/terrakko vm shutdown` または `/terrakko vm stop` で停止してから削除してください。

## 操作の通知について

- 各コマンドの実行受付は、チャンネルに **Ephemeral メッセージ**（自分にのみ表示）で即時通知されます。
- 非同期処理の完了（またはエラー）は **DM** で通知されます。
- DM の受信が無効になっている場合は、代わりにチャンネルへ Ephemeral メッセージで通知されます。
- 操作の監視タイムアウトは **15 分**です。タイムアウト後は `/terrakko vm status` で現在の状態を確認してください。
