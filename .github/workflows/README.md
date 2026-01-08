# GitHub Actions Workflows

このディレクトリには、Terrakkoプロジェクトの自動化されたCI/CDパイプラインが含まれています。

## ワークフロー一覧

### 1. CI/CD Pipeline (`ci.yml`)

**トリガー:**
- `main`, `develop`, `feat/*` ブランチへのプッシュ
- `main`, `develop` ブランチへのプルリクエスト

**ジョブ:**
- **Test**: Node.js 18.x, 20.x, 22.x でテスト実行
  - 依存関係のインストール
  - better-sqlite3のネイティブバインディング再構築
  - Jestテスト実行
  - カバレッジレポート生成
  - Codecovへのアップロード

- **Build**: TypeScriptのビルド確認
  - TypeScriptコンパイル
  - distディレクトリの確認
  - ビルド成果物のアップロード

- **Lint**: コード品質チェック
  - TypeScript型チェック

- **Security**: セキュリティ監査
  - npm audit実行
  - 脆弱性チェック

- **Docker Build**: Dockerイメージビルドテスト（main/developのみ）

- **Summary**: 全ジョブの結果サマリー

### 2. Pull Request Checks (`pr-checks.yml`)

**トリガー:**
- プルリクエストのオープン、同期、再オープン

**ジョブ:**
- **PR Validation**: PRタイトルの検証
  - Conventional Commitsフォーマットチェック
  - マージコンフリクトチェック

- **Quick Test**: 高速テスト（Node.js 20.xのみ）

- **Code Review**: 自動コードレビュー
  - TODO/FIXMEコメント検出
  - 大きなファイルの検出
  - テストカバレッジ確認

- **Comment Summary**: PRへのコメント投稿

### 3. Release (`release.yml`)

**トリガー:**
- `v*.*.*` 形式のタグプッシュ

**ジョブ:**
- **Create Release**: GitHubリリースの作成
  - テストとビルド実行
  - 配布パッケージ作成
  - 変更履歴生成
  - リリースノート作成

- **Build Docker**: Dockerイメージのビルドとプッシュ
  - マルチアーキテクチャビルド（amd64, arm64）
  - Docker Hubへのプッシュ

- **Notify Release**: リリース通知

### 4. Scheduled Checks (`scheduled-checks.yml`)

**トリガー:**
- 毎日00:00 UTC（cron）
- 手動トリガー（workflow_dispatch）

**ジョブ:**
- **Dependency Audit**: 依存関係のセキュリティ監査
  - npm audit実行
  - 古い依存関係チェック
  - レポート生成

- **Test Matrix**: 拡張テストマトリックス
  - 複数OS（Ubuntu, macOS, Windows）
  - 複数Node.jsバージョン

- **Code Quality**: コード品質チェック
  - カバレッジ閾値確認（70%以上）
  - コード複雑度チェック

- **Integration Test**: 統合テストシミュレーション

- **Summary**: 日次チェックサマリー

## 必要なシークレット

以下のシークレットをGitHubリポジトリの設定で追加してください:

- `DOCKER_USERNAME`: Docker Hubのユーザー名（リリース時のDockerイメージプッシュ用）
- `DOCKER_PASSWORD`: Docker Hubのパスワード/トークン
- `CODECOV_TOKEN`: Codecovトークン（オプション、カバレッジアップロード用）

## ローカルでのテスト

### 依存関係のインストール

```bash
cd app
npm install
```

### テスト実行

```bash
# すべてのテストを実行
npm test

# カバレッジ付きテスト
npm run test:coverage

# ウォッチモード
npm run test:watch
```

### ビルド実行

```bash
# TypeScriptビルド
npm run build

# ビルド成果物の確認
ls -la dist/
```

### 型チェック

```bash
# TypeScript型チェック（ビルドせずに）
npx tsc --noEmit
```

## ワークフローのステータス

各ワークフローのステータスは、READMEのバッジで確認できます:

- [![CI/CD Pipeline](https://github.com/nekko-lab/terrakko/actions/workflows/ci.yml/badge.svg)](https://github.com/nekko-lab/terrakko/actions/workflows/ci.yml)

## トラブルシューティング

### better-sqlite3のビルドエラー

```bash
# ネイティブバインディングを再構築
npm rebuild better-sqlite3
```

### テスト失敗

```bash
# 詳細なログでテスト実行
npm test -- --verbose

# 特定のテストファイルのみ実行
npm test -- Validator.test.ts
```

### ビルドエラー

```bash
# 型エラーの詳細確認
npx tsc --noEmit

# distディレクトリをクリーンアップ
rm -rf dist && npm run build
```

## ベストプラクティス

1. **コミット前**: ローカルでテストとビルドを実行
   ```bash
   npm test && npm run build
   ```

2. **PR作成前**: Conventional Commitsに従う
   - `feat:` 新機能
   - `fix:` バグ修正
   - `docs:` ドキュメント更新
   - `test:` テスト追加・修正
   - `refactor:` リファクタリング

3. **カバレッジ維持**: 新しいコードには必ずテストを追加
   - 最低カバレッジ: 70%
   - 目標カバレッジ: 80%以上

4. **セキュリティ**: 定期的に依存関係を更新
   ```bash
   npm outdated
   npm audit fix
   ```

## 参考資料

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Jest Documentation](https://jestjs.io/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
