#!/bin/bash

# Docker開発環境スクリプト
# Docker コンテナを起動して開発環境に入る

set -e

echo "🐳 Docker開発環境を起動中..."

# Docker イメージをビルド
docker compose build

# Docker コンテナを起動してbashシェルに入る
docker compose run --rm nil bash

echo "✅ 開発環境を終了しました"