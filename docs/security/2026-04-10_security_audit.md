# Security Audit Report: Terrakko (2026-04-10)

## 1. Executive Summary
Terrakko の現在の実装には、パブリック公開を阻害する深刻な脆弱性が複数確認されました。特に Proxmox 管理者権限の漏洩リスクおよび通信の暗号化不備は、最優先で修正が必要です。

## 2. Critical Vulnerabilities (Priority: High)

### 2.1. Administrative Credential Leakage (PVE_PASS)
- **Issue:** `app/src/terrakko.py` (L1070付近) において、新規ユーザー登録時の初期パスワードとして Proxmox サーバーの管理者パスワード (`PVE_PASS`) がそのまま流用されています。
- **Risk:** ユーザーが自分の VM にログインするパスワードを知ることで、間接的に Proxmox 本体の管理パスワードを入手でき、システム全体へのフルアクセスを許す可能性があります。
- **Countermeasure:** 管理者パスワードの流用を即座に停止。初期パスワードはランダム生成するか、初回操作時にユーザーに設定（Modal入力）させる。

### 2.2. SSL/TLS Verification Disabled
- **Issue:** `app/src/proxmox_ve.py` において、`verify_ssl=False` が設定されている、または証明書の検証が行われていません。
- **Risk:** 中間者攻撃 (MITM) により、Discord Bot と Proxmox 間の API 通信（パスワードやトークンを含む）が傍受・改ざんされるリスクがあります。
- **Countermeasure:** `verify_ssl` を有効化し、適切な CA 証明書を運用環境で指定する。

## 3. Implementation & Maintenance Risks (Priority: Medium)

### 3.1. Plaintext Password Exposure in UI
- **Issue:** Discord のメッセージ（Ephemeral 含む）にパスワードを平文で表示している箇所があります。
- **Risk:** Discord サーバー側のログや、画面共有・物理的な覗き見による漏洩リスク。
- **Countermeasure:** 表示をマスクする、またはパスワードを表示するプロセス自体を廃止（秘密情報はユーザー側で管理）。

### 3.2. Deprecated Hashing (crypt module)
- **Issue:** `crypt` モジュールは Python 3.13 で削除予定です。
- **Risk:** 将来的な Python バージョンアップに伴う動作停止。
- **Countermeasure:** `passlib` 等のモダンなライブラリへ完全に移行する。

### 3.3. SQL Injection Potential
- **Issue:** `db.py` の `get_column` 関数等で、動的なカラム指定をクエリに埋め込んでいます。
- **Risk:** 内部呼び出し限定であっても、将来の拡張時に意図しないクエリ実行を許すリスクがあります。
- **Countermeasure:** プリペアドステートメントの徹底、または前述の「ステートレス化」による DB 廃止。

### 3.4. Insecure Docker Configuration
- **Issue:** Dockerfile が root ユーザーでプロセスを実行しています。
- **Risk:** コンテナ脱出脆弱性が発生した際、ホスト OS 全体への影響が拡大します。
- **Countermeasure:** 一般ユーザー (`appuser` 等) を作成し、最小権限で実行する。

## 4. Remediation Roadmap
1. **Immediate:** 管理者パスワード流用の停止、SSL 検証のデフォルト有効化。
2. **Next Step:** タグベースの所有権管理への移行、DB の廃止。
3. **UI/UX:** スラッシュコマンド化による入力支援とノイズ削減。
