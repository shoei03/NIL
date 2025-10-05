# Docker 環境スクリプト

このディレクトリには、Docker 環境で NIL プロジェクトを操作するためのシェルスクリプトが含まれています。

## スクリプト一覧

### `dev.sh` - 開発環境

Docker コンテナを起動して、対話的な開発環境に入ります。

```bash
./scripts/dev.sh
```

### `build.sh` - ビルド

NIL プロジェクトをビルドして、実行可能な JAR ファイルを生成します。

```bash
./scripts/build.sh
```

### `run.sh` - 実行

NIL アプリケーションを実行します。引数も渡すことができます。

```bash
./scripts/run.sh [NILオプション...]
./scripts/run.sh --help  # ヘルプ表示
```

### `nil.sh` - NIL クローン検出実行

よく使われるオプションで NIL を簡単に実行するための便利スクリプトです。

```bash
./scripts/nil.sh <ソースディレクトリ> [オプション...]
```

### `test.sh` - テスト

テストを実行します。

```bash
./scripts/test.sh
```

### `clean.sh` - クリーンアップ

Docker リソースと Gradle キャッシュをクリーンアップします。

```bash
./scripts/clean.sh
```

## 注意事項

- すべてのスクリプトはプロジェクトルートから実行してください
- `docker compose` コマンドを使用しています（`docker-compose` ではありません）
- エラーが発生した場合、スクリプトは自動的に停止します（`set -e`）
- ビルド前に NIL を実行しようとするとエラーメッセージが表示されます
