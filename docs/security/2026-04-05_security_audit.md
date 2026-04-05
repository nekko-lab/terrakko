# セキュリティ脆弱性診断レポート

- **診断日時**: 2026-04-05
- **対象プロジェクト**: Terrakko v1.0.2
- **特定された技術スタック**: Python 3.11 / discord.py / proxmoxer / aiosqlite (SQLite) / Docker
- **総合セキュリティ評価**: **2 / 5**
- **DAST**: 実施不可（静的解析のみ）

---

## 1. エグゼクティブサマリー

Proxmox VE への接続で SSL 検証が無効化されており、MITM 攻撃のリスクがある。  
また新規ユーザー登録時に Proxmox の管理者パスワードを初期 VM パスワードとして流用しており、認証情報の漏洩経路となる恐れがある。  
`crypt` モジュールは Python 3.11 時点で非推奨・Python 3.13 で削除済みのため、Docker イメージを更新すると起動不能になる時限的な問題も存在する。  
依存パッケージは複数バージョンが古く、既知 CVE の有無について手動照合が必要な状態である。

---

## 2. 依存関係の脆弱性 (SCA) — 評価: **3 / 5**

- **使用ツール**: PyPI 最新バージョン手動照合（`pip-audit` / `safety` は環境未インストール）
- **Critical**: 0件（確認できた範囲）/ **High**: 0件 / **Medium**: 1件 / **Low**: 3件

| パッケージ | 使用バージョン | 最新バージョン | 影響度 | 備考 |
|:---|:---:|:---:|:---:|:---|
| `proxmoxer` | 2.1.0 | **2.3.0** | Medium | 2マイナー遅れ。変更履歴の確認推奨 |
| `discord.py` | 2.4.0 | **2.7.1** | Low | 3マイナー遅れ |
| `urllib3` | 2.2.3 | **2.6.3** | Low | 過去に CVE あり。更新推奨 |
| `requests` | 2.32.3 | **2.33.1** | Low | urllib3 に依存するため連動更新 |
| `aiosqlite` | 0.20.0 | 0.22.1 | Low | マイナーアップデートのみ |
| `python-dotenv` | 1.0.1 | 1.2.2 | Low | マイナーアップデートのみ |
| `asyncio` | 3.4.3 | — | **Medium** | asyncio は Python 3.4 以降の**標準ライブラリ**。PyPI 版を pip install すると標準ライブラリを上書きする危険がある。`requirements.txt` から削除すべき |

**推奨アクション**: `asyncio` を `requirements.txt` から削除。他パッケージは最新版に更新し `pip-audit` を CI に組み込む。

---

## 3. 静的解析結果 (SAST) — 評価: **2 / 5**

### 3-1. シークレット管理

| 評価 | 詳細 |
|:---:|:---|
| ✅ | シークレット類は `.env` ファイル経由で `os.getenv()` 取得しており、ソースコードへのハードコードはなし |
| ✅ | `.dockerignore` に `.env*` が含まれており、コンテナイメージへの混入を防止している |
| ✅ | `.gitignore` に `db/` と `app/node_modules/` が追加されている |

---

### 3-2. 危険なコードパターン

#### 🔴 Critical: Proxmox VE への SSL 検証無効

**ファイル**: [proxmox_ve.py:72](../../app/src/proxmox_ve.py#L72)

```python
pve = ProxmoxAPI(..., verify_ssl=False)
```

`verify_ssl=False` は TLS 証明書を検証しない。同一ネットワーク上での MITM 攻撃により、Proxmox API のレスポンスが改ざんされると VM 操作が乗っ取られる可能性がある。Proxmox VE に自己署名証明書を使用している場合でも、CA バンドルを指定する方法が proxmoxer 2.x で利用可能。

**対応**: 自己署名証明書の場合は `verify_ssl="/path/to/ca.pem"` を指定する。

---

#### 🔴 High: 管理者パスワードを新規ユーザーの VM 初期パスワードに流用

**ファイル**: [terrakko.py:1070](../../app/src/terrakko.py#L1070)

```python
await db.insert_data(ctx.author.id, "ncadmin", config.PVE_PASS, "")
```

`config.PVE_PASS`（Proxmox 管理者パスワード）を cloud-init の初期パスワードとして全ユーザーの VM に設定している。  
VM にアクセスできるユーザー全員が Proxmox 管理者パスワードを知ることになる。また SSH 鍵が空文字列で登録される。

**対応**: 初期パスワードはランダム生成するか、ユーザーに入力させる。`PVE_PASS` は VM パスワードに使用しない。

---

#### 🔴 High: `crypt` モジュールの非推奨・削除問題

**ファイル**: [db.py:13](../../app/src/db.py#L13), [db.py:71](../../app/src/db.py#L71)

```python
import crypt
crypt.crypt(password, crypt.METHOD_SHA512)
```

`crypt` モジュールは Python 3.11 で DeprecationWarning、**Python 3.13 で完全削除**。  
現在の Dockerfile は `python:3.11-slim` を使用しているため動作するが、イメージを更新すると即座に起動不能になる。代替は `passlib` ライブラリ（`sha512_crypt`）または Python 3.9+ の `hashlib` + `crypt` 互換実装。

**対応**: `passlib[bcrypt]` または `passlib[sha512_crypt]` への移行を推奨。

---

#### 🟠 Medium: 確認メッセージでパスワード平文を Discord に送信

**ファイル**: [terrakko.py:752](../../app/src/terrakko.py#L752)

```python
await interaction.response.send_message(
    f"Password:\t||{self.cipass}||\n...", ephemeral=True
)
```

`self.cipass` はフォームから取得した**平文パスワード**であり、DB 保存前の段階で Discord の ephemeral メッセージに表示される。ephemeral は他ユーザーには見えないが、Discord サーバー側にはログが残る可能性がある。

**対応**: パスワードは確認メッセージに含めず `(set)` など伏せる形にする。

---

#### 🟠 Medium: `get_column()` の SQL インジェクション脆弱性

**ファイル**: [db.py:128](../../app/src/db.py#L128)

```python
await cur.execute(f"SELECT {column} FROM {config.dbname}")
```

`column` がプレースホルダー `?` ではなく f-string で直接埋め込まれている。現在の呼び出し箇所（terrakko.py:1062）はハードコードされた `"uuid"` のみだが、関数のインターフェース上はユーザー入力が渡せる状態。将来的な拡張時に SQL インジェクションになるリスクがある。

**対応**: テーブル名・カラム名はホワイトリスト検証を行う（SQLite はカラム名のプレースホルダーをサポートしていないため）。

---

#### 🟡 Low: `re.match()` にユーザー ID を直接埋め込み（ReDoS リスク）

**ファイル**: [proxmox_ve.py:350](../../app/src/proxmox_ve.py#L350), [terrakko.py:541](../../app/src/terrakko.py#L541)

```python
re.match(f"{author_id}", vm['name'])
re.match(f"{interaction.user.id}", val[2])
```

Discord のユーザー ID は整数のため現時点では悪用不可だが、ユーザー制御データを regex パターンに直接埋め込む実装は ReDoS の温床になる。また所有権確認として `str(author_id)` の前方一致で済む処理に regex は不要。

**対応**: `val[2].startswith(str(interaction.user.id))` などシンプルな文字列比較に置き換える。

---

#### 🟡 Low: `interaction.data` のログ出力

**ファイル**: [terrakko.py:202](../../app/src/terrakko.py#L202)

```python
print(f"{interaction.user.id} is now operating {interaction.data}")
```

`interaction.data` にはボタン・モーダルの入力値が含まれる場合があり、ユーザーの操作内容がコンテナログに出力される。本番運用でログを外部に転送している場合は注意が必要。

---

### 3-3. セキュリティ設定

| 評価 | 詳細 |
|:---:|:---|
| ✅ | DB への値渡しは `CREATE TABLE` を除きすべてプレースホルダー `?` を使用 |
| ✅ | Discord UI は全て `ephemeral=True` でユーザー本人にのみ表示 |
| ✅ | ユーザー ID の所有権確認は各操作で実施されている |
| ⚠️ | `verify_ssl=False` により PVE API 通信が非暗号化相当になっている（前述） |
| ⚠️ | Docker コンテナが `root` ユーザーで動作している（Dockerfile に `USER` 指定なし） |

---

## 4. 動的検証結果 (DAST) — **実施なし**

ユーザー指示により今回は省略。  
実施可能になった際の確認推奨項目:
- コンテナログへの機密情報出力の有無
- Discord API との通信が HTTPS のみか
- Proxmox VE への接続で実際に証明書検証がスキップされているか

---

## 5. 推奨対応策 (Remediation)

### 優先度: Critical / High

| # | 問題 | 対応 |
|---|------|------|
| 1 | SSL 検証無効 | `verify_ssl` に CA 証明書パスを指定する（`verify_ssl="/etc/ssl/certs/ca-certificates.crt"` など） |
| 2 | 管理者パスワードの流用 | 初期パスワードをランダム生成（`secrets.token_urlsafe(16)`）するか、初回ログイン時にユーザーに設定させる |
| 3 | `crypt` モジュール削除問題 | `requirements.txt` に `passlib[sha512_crypt]` を追加し `db.py` の実装を置き換える |

### 優先度: Medium

| # | 問題 | 対応 |
|---|------|------|
| 4 | パスワード平文を Discord に表示 | `SetUserInfoForm.on_submit` の確認メッセージからパスワードを除外 |
| 5 | `get_column()` SQL インジェクション | カラム名をホワイトリスト検証（`if column not in ("uuid", "username", "sshkey"): raise ValueError`） |
| 6 | `asyncio` の PyPI 版インストール | `requirements.txt` から `asyncio==3.4.3` を削除 |

### 優先度: Low

| # | 問題 | 対応 |
|---|------|------|
| 7 | ReDoS リスクのある regex | `re.match` を `str.startswith` に置き換え |
| 8 | コンテナが root 動作 | Dockerfile に `RUN useradd -m appuser && USER appuser` を追加 |
| 9 | `interaction.data` ログ出力 | 本番では操作ログからデータ内容を除外する |
| 10 | 依存パッケージの古さ | `pip-audit` を CI に組み込み、定期的に更新する |
