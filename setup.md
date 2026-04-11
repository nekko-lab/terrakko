# Terrakko セットアップ

## 1. Proxmox VE

### ロールとユーザーの作成

`TerrakkoAccess` ロールを作成します。

```shell
pveum role add TerrakkoAccess -privs "VM.Clone,VM.Monitor,VM.PowerMgmt,VM.Audit,VM.Allocate,VM.Config.Cloudinit,VM.Config.Options,SDN.Use,Datastore.AllocateSpace"
```

サービスアカウント `terrakko-agent@pve` を作成し、ロールを付与します。

```shell
pveum user add terrakko-agent@pve --password $PASSWORD
pveum aclmod / -user terrakko-agent@pve -role TerrakkoAccess
```

### API トークンの発行

```shell
$ pvesh create /access/users/terrakko-agent@pve/token/terrakko --privsep 0
┌──────────────┬──────────────────────────────────────┐
│ key          │ value                                │
╞══════════════╪══════════════════════════════════════╡
│ full-tokenid │ terrakko-agent@pve!terrakko          │
├──────────────┼──────────────────────────────────────┤
│ value        │ xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx │
└──────────────┴──────────────────────────────────────┘
```

`full-tokenid` が `PVE_USER!PVE_TOKEN`、`value` が `PVE_SECRET` に対応します。

### VM テンプレートの作成

Cloud-init 対応の VM テンプレートが各ノードに必要です。VMID は 90000 以上に設定してください。

テンプレート作成には Ansible を利用できます:  
[nekko-cloud](https://github.com/nekko-lab/nekko-cloud/tree/5eb88569918a52e2e92dccbc407bc39ed353c473/iaas/cloudinit)

### リソースプールによるアクセス制限（任意）

<details>
<summary>詳細</summary>

- `terrakko-agent@pve` ユーザーをアクセス可能なリソースプールのメンバーに追加
- アクセスを許可するプールには `TerrakkoAccess` ロールを付与
- アクセスを禁止するプールには `NoAccess` ロールを付与

</details>

---

## 2. Discord

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーションを作成
2. Bot を作成し、Bot Token を取得
3. `applications.commands` スコープで Guild Install URL を生成してサーバーにインストール

---

## 3. デプロイ

リポジトリをクローンし、`app/` ディレクトリに `.env` ファイルを作成します。

```shell
git clone <repository_url>
cd terrakko/app
cp .env.temp .env
# .env を編集して各値を設定
```

`.env` の設定項目については [config.md](config.md) を参照してください。

### Docker Compose で起動

```shell
cd app
docker compose up -d --build
```

---

## 4. SSL 証明書の設定

Proxmox VE が自己署名証明書または独自 CA を使用している場合は、`PVE_CA_CERT` に CA 証明書のパスを指定してください。

```
PVE_CA_CERT=/path/to/ca.crt
```

空のままにするとシステムの CA バンドルを使用します（公的 CA 署名証明書の場合はこれで問題ありません）。
