# セキュリティ脆弱性診断レポート

- **診断日時**: 2026-04-12
- **対象プロジェクト**: Terrakko (nekko-lab/terrakko)
- **特定された技術スタック**: Python 3.14, discord.py 2.7.1, proxmoxer 2.3.0, Docker
- **総合セキュリティ評価**: 4 / 5

---

## 1. エグゼクティブサマリー

依存パッケージに既知の脆弱性はなく、シークレットのハードコードや `.env` のコミット履歴も確認されなかった。SSL 検証はデフォルト有効であり、コマンドインジェクションにつながる危険なパターンも存在しない。公開リポジトリとしてリリース可能な状態だが、コマンドのレート制限不在と `.claude/` ディレクトリの `.gitignore` 未記載の 2 点を対処することを推奨する。

---

## 2. 依存関係の脆弱性 (SCA) — 評価: 5 / 5

- **使用ツール**: pip-audit (venv 経由)
- **Critical**: 0件 / **High**: 0件 / **Medium**: 0件 / **Low**: 0件

| パッケージ | バージョン | 結果 |
|:---|:---:|:---|
| discord.py | 2.7.1 | 問題なし |
| proxmoxer | 2.3.0 | 問題なし |
| python-dotenv | 1.2.2 | 問題なし |
| requests | 2.33.1 | 問題なし |
| urllib3 | 2.6.3 | 問題なし |

---

## 3. 静的解析結果 (SAST) — 評価: 4 / 5

### シークレット管理

| 確認項目 | 結果 |
|:---|:---|
| ソースコードへのハードコード | **問題なし** — 全シークレットは `os.getenv()` 経由 |
| `.env` の git 追跡 | **問題なし** — `.gitignore` の `.env*` パターンで除外済み |
| git 履歴への `.env` コミット | **問題なし** — 全コミット履歴を確認、実 `.env` はゼロ件 |
| `config.md` のサンプル値 | **問題なし** — `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` 等のダミー値のみ |
| CA 証明書の管理 | **問題なし** — `certs/` は `.gitignore` で除外済み |

### 危険なコードパターン

| 確認項目 | 結果 |
|:---|:---|
| `subprocess` / `os.system` / `eval()` / `exec()` | **問題なし** — 該当なし |
| SQL インジェクション | **問題なし** — DB 使用なし |
| コマンドインジェクション | **問題なし** — 外部コマンド実行なし |
| SSL 検証の無効化 (`verify_ssl=False`) | **問題なし** — デフォルト `True`、カスタム CA パス対応 |
| ユーザー入力の直接ログ出力 | **修正済み** — `on_interaction` はコマンド名のみ出力（SSH鍵等を含む `interaction.data` の直接出力を修正）|

### セキュリティ設定

| 確認項目 | 結果 |
|:---|:---|
| Docker 非 root 実行 | **問題なし** — `user: "1000:1000"` (appuser) |
| GitHub Actions 権限 | **問題なし** — `GITHUB_TOKEN` のみ使用、最小権限 |
| 本番 compose のボリューム | **問題なし** — `docker-compose.prod.yaml` はプリビルドイメージ使用、ソースマウントなし |

### 要改善項目（Medium）

#### 1. コマンドのレート制限不在

- **場所**: `app/src/terrakko.py` — `/terrakko vm build` 等全コマンド
- **内容**: 1ユーザーが短時間に `/terrakko vm build` を連打した場合、PVE 上に大量の VM が作成される可能性がある。Nekko Cloud のクローズドコミュニティ向けのため即時リリースブロックではないが、対処を推奨。
- **推奨対応**: discord.py の `app_commands.checks.cooldown` デコレータ、または `active_sessions` を拡張した per-user カウンターで建設前の上限を設ける。

#### 2. `.claude/` ディレクトリが `.gitignore` に未記載

- **場所**: `.gitignore`
- **内容**: `.claude/settings.local.json` は現在 git 未追跡だが、`.gitignore` に明示されていない。将来的に誤って `git add .` された場合、Claude Code のローカル設定（ツール許可等）が公開される可能性がある。
- **推奨対応**: `.gitignore` に `.claude/` と `.jj/` を追加する。

### 軽微な懸念（Low）

#### 3. 例外メッセージのログ出力

- **場所**: `app/src/proxmox_ve.py` — 複数箇所（例: 244行, 277行）
- **内容**: `print(f"Creation failed: {e}")` のように例外オブジェクトをそのまま出力している。PVE の内部エラーメッセージに IP アドレスやノード名が含まれる場合があるが、ログはコンテナ内に留まり外部公開されないため低リスク。
- **推奨対応**: 本番運用開始後、`logging` モジュールへの移行と出力先のコントロールを検討。

---

## 4. 動的検証結果 (DAST) — 評価: N/A

Discord Bot はリッスンする HTTP エンドポイントを持たないため、従来の DAST スキャンは非該当。  
実行時に外部通信するエンドポイントは以下の 3 つのみで、いずれも TLS 通信を使用する。

| 通信先 | 用途 | TLS |
|:---|:---|:---:|
| Proxmox VE API (`PVE_HOST`) | VM 操作 | ✓ (`verify_ssl` 有効) |
| Discord API | Bot 通信 | ✓ (discord.py 内部) |
| bw-agent (`BW_AGENT_URL`) | パスワード配送 | 任意 (内部ネットワーク想定) |

---

## 5. 推奨対応策 (Remediation)

### 優先度: Medium（リリース前推奨）

**1. コマンドレート制限の追加**

```python
from discord.ext.commands import cooldown, BucketType

@vm_group.command(name="build", ...)
@app_commands.checks.cooldown(rate=3, per=60.0, key=lambda i: i.user.id)
async def vm_build(...):
    ...
```

ユーザーごとに 60 秒間に 3 回まで等の制限を設ける。

**2. `.gitignore` への明示追加**

`.gitignore` の末尾に以下を追加する:

```
.claude/
.jj/
```

### 優先度: Low（運用開始後）

**3. `logging` モジュールへの移行**

`print()` を `logging` モジュールに置き換えることで、ログレベルの制御と出力先の分離が可能になる。本番環境では `WARNING` 以上のみ出力するよう設定することを推奨。

---

## 6. 総括

公開リポジトリとして問題となる情報漏洩・既知脆弱性は確認されなかった。Medium 1件（レート制限）と Low 2件（`.gitignore`、例外ログ）が残存するが、クローズドコミュニティ向けツールとしての公開はリスク許容範囲内と判断する。

| フェーズ | 評価 |
|:---|:---:|
| SCA（依存関係） | 5 / 5 |
| SAST（静的解析） | 4 / 5 |
| DAST（動的検証） | N/A |
| **総合** | **4 / 5** |
