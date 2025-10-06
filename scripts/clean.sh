#!/bin/bash

# クリーンアップスクリプト
# Docker リソースをクリーンアップする

set -e

echo "🧹 Docker リソースをクリーンアップ中..."

# Docker コンテナを停止・削除
docker compose down

# Gradleキャッシュをクリーンアップ
echo "📦 Gradleキャッシュをクリーンアップ中..."
docker compose run --rm nil ./gradlew clean

# 使用されていないDockerイメージを削除（オプション）
read -p "❓ 使用されていないDockerイメージも削除しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  使用されていないDockerイメージを削除中..."
    docker image prune -f
fi

echo "✅ クリーンアップが完了しました"