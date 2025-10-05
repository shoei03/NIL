#!/bin/bash

# テスト実行スクリプト
# Docker環境でテストを実行する

set -e

echo "🧪 テストを実行中..."

# Docker コンテナでGradleテストを実行
docker compose run --rm nil java -jar ./build/libs/NIL-all.jar -s "/app/src/test/resources/samples" -l "python" -o "./results/test.csv"

echo "✅ テストが完了しました"
echo "📊 テスト結果: ./results/test.csv"