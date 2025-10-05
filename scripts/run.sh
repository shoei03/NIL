#!/bin/bash

# アプリケーション実行スクリプト
# Docker環境でNILアプリケーションを実行する

set -e

echo "🚀 NILを実行中..."

# JARファイルが存在するかチェック
if ! docker compose run --rm nil test -f ./build/libs/NIL-all.jar; then
    echo "❌ NIL-all.jarが見つかりません。先にビルドを実行してください："
    echo "   ./scripts/build.sh"
    exit 1
fi

# 引数があれば渡す、なければヘルプを表示
if [ $# -eq 0 ]; then
    echo "ℹ️  使用方法を表示します..."
    docker compose run --rm nil java -jar ./build/libs/NIL-all.jar --help
else
    docker compose run --rm nil java -jar ./build/libs/NIL-all.jar "$@"
fi

echo "✅ NILの実行が完了しました"