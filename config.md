# 設定リファレンス

## 環境変数（`.env`）

### Proxmox VE

| 変数 | 必須 | 説明 |
| ---- | ---- | ---- |
| `PVE_HOST` | ✓ | Proxmox VE のホスト IP またはホスト名 |
| `PVE_USER` | ✓ | API ユーザー（例: `terrakko-agent@pve`） |
| `PVE_TOKEN` | ✓ | API トークン名（例: `terrakko`） |
| `PVE_SECRET` | ✓ | API トークンのシークレット値 |
| `PVE_TEMP_NAME` | ✓ | 使用する VM テンプレート名（例: `ubuntu24.04-General-template-v1.0.0`） |
| `PVE_POOL` | — | VM を作成するリソースプール名。空の場合はプール指定なしで作成 |
| `PVE_CA_CERT` | — | CA 証明書のファイルパス。空の場合はシステム CA バンドルを使用 |

`PVE_USER`、`PVE_TOKEN`、`PVE_SECRET` は `pvesh create /access/users/.../token/...` で取得した値を設定します。

### Discord Bot

| 変数 | 必須 | 説明 |
| ---- | ---- | ---- |
| `DISCORD_TOKEN` | ✓ | Discord Bot Token |
| `DISCORD_GUILD_ID` | — | ギルド ID。設定するとコマンドが即時反映（開発向け）。空の場合はグローバル同期（最大1時間） |

### bw-agent（パスワード配送）

| 変数 | 必須 | 説明 |
| ---- | ---- | ---- |
| `BW_AGENT_URL` | — | bw-agent の内部 URL（例: `http://bw-agent:8080`）。未設定の場合はパスワード共有をスキップし、PVE コンソールから変更するよう案内する |

### Docker

| 変数 | 必須 | 説明 |
| ---- | ---- | ---- |
| `WORKDIR` | ✓ | コンテナ内のワーキングディレクトリ名 |
| `DOMAIN` | — | VM のホスト名サフィックス（例: `.nekko.cloud`） |

---

## アプリケーション設定（`config.py`）

| 定数 | デフォルト | 説明 |
| ---- | ---------- | ---- |
| `TIME` | `900` | PVE タスク監視のタイムアウト秒数（15 分） |

---

## `.env` ファイルのテンプレート

```dotenv
# Proxmox VE
PVE_HOST=192.168.1.10
PVE_USER=terrakko-agent@pve
PVE_TOKEN=terrakko
PVE_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PVE_TEMP_NAME=ubuntu24.04-General-template-v1.0.0
PVE_CA_CERT=

# Discord
DISCORD_TOKEN=your_discord_bot_token

# bw-agent
BW_AGENT_URL=http://bw-agent:8080

# Docker
WORKDIR=src
DOMAIN=.example.com
```
