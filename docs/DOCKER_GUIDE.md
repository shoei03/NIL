# NIL Docker 実行ガイド

このドキュメントでは、NIL を Docker コンテナ内で実行する方法について詳しく説明します。

## 目次

1. [Docker イメージについて](#dockerイメージについて)
2. [セットアップ手順](#セットアップ手順)
3. [実行方法](#実行方法)
4. [ユースケース別実行例](#ユースケース別実行例)
5. [トラブルシューティング](#トラブルシューティング)
6. [カスタマイズ](#カスタマイズ)

---

## Docker イメージについて

### ベースイメージ

```dockerfile
FROM openjdk:21-jdk-slim
```

- **Java**: OpenJDK 21
- **OS**: Debian-based slim image
- **追加ツール**: git

### イメージサイズ

- ベースイメージ: 約 400MB
- ビルド後（NIL 含む）: 約 450MB

### 含まれているツール

- Java Development Kit 21
- Git
- Gradle（Gradle Wrapper 経由）
- NIL ソースコード

---

## セットアップ手順

### 前提条件

以下のソフトウェアがインストールされている必要があります：

- Docker Engine 20.10+
- Docker Compose 1.29+（方法 1 を使用する場合）

### インストール確認

```bash
# Dockerバージョン確認
docker --version

# Docker Composeバージョン確認
docker-compose --version
```

### 初回セットアップ

#### 方法 1: Docker Compose を使用（推奨）

```bash
# 1. リポジトリをクローン
git clone https://github.com/kusumotolab/NIL
cd NIL

# 2. Dockerイメージをビルド
docker-compose build

# 3. コンテナを起動
docker-compose up -d

# 4. コンテナに入る
docker-compose exec nil bash

# 5. NILをビルド
./gradlew shadowJar

# 6. ビルド確認
ls -lh ./build/libs/NIL-all.jar
```

#### 方法 2: Docker コマンドを直接使用

```bash
# 1. リポジトリをクローン
git clone https://github.com/kusumotolab/NIL
cd NIL

# 2. Dockerイメージをビルド
docker build -t nil:latest .

# 3. コンテナを起動
docker run -it -v $(pwd):/app -w /app nil:latest bash

# 4. NILをビルド
./gradlew shadowJar

# 5. ビルド確認
ls -lh ./build/libs/NIL-all.jar
```

---

## 実行方法

### 基本的な実行フロー

```bash
# 1. コンテナを起動（まだ起動していない場合）
docker-compose up -d

# 2. コンテナに入る
docker-compose exec nil bash

# 3. NILを実行
java -jar ./build/libs/NIL-all.jar -s <ソースディレクトリ> [オプション]

# 4. 結果を確認
cat result_*.csv

# 5. コンテナから退出
exit

# 6. コンテナを停止（必要に応じて）
docker-compose down
```

### ワンライナー実行

コンテナに入らずに直接実行する方法：

```bash
docker-compose exec nil java -jar ./build/libs/NIL-all.jar \
  -s /app/Repos/pandas \
  -l py \
  -o /app/results/pandas_clones.csv
```

### バックグラウンド実行

長時間かかる処理をバックグラウンドで実行：

```bash
docker-compose exec -d nil java -jar ./build/libs/NIL-all.jar \
  -s /app/Repos/large-project \
  -p 135 \
  -t 16 \
  -o /app/results/output.csv
```

ログを確認：

```bash
docker-compose logs -f nil
```

---

## ユースケース別実行例

### 1. ローカルプロジェクトの解析

ホストマシンのプロジェクトをマウントして解析：

```bash
# docker-compose.ymlを編集して追加のボリュームをマウント
# services:
#   nil:
#     volumes:
#       - .:/app
#       - /path/to/your/project:/workspace/project

docker-compose up -d
docker-compose exec nil java -jar ./build/libs/NIL-all.jar \
  -s /workspace/project \
  -l java \
  -o /app/results/my_project_clones.csv
```

### 2. GitHub リポジトリのクローン検出

```bash
docker-compose exec nil bash

# リポジトリをクローン
git clone https://github.com/username/repository.git /app/Repos/repository

# NILを実行
java -jar ./build/libs/NIL-all.jar \
  -s /app/Repos/repository \
  -l java \
  -o /app/results/repository_clones.csv

exit
```

### 3. 複数プロジェクトの一括解析

シェルスクリプトを使用した一括解析：

```bash
# analyze_all.shをコンテナ内で作成
docker-compose exec nil bash

cat > /app/analyze_all.sh << 'EOF'
#!/bin/bash

REPOS_DIR="/app/Repos"
RESULTS_DIR="/app/results"

for repo in "$REPOS_DIR"/*; do
    if [ -d "$repo" ]; then
        repo_name=$(basename "$repo")
        echo "Analyzing $repo_name..."

        java -jar /app/build/libs/NIL-all.jar \
            -s "$repo" \
            -l java \
            -o "$RESULTS_DIR/${repo_name}_clones.csv" \
            2>&1 | tee "$RESULTS_DIR/${repo_name}_log.txt"
    fi
done

echo "All analyses completed!"
EOF

chmod +x /app/analyze_all.sh
./analyze_all.sh

exit
```

### 4. 特定コミットの解析（追跡機能付き）

```bash
docker-compose exec nil bash

cd /app/Repos/pandas

# 特定のコミットをチェックアウト
git checkout <commit-hash>

# コミット情報を取得
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_TIME=$(git log -1 --format=%cd --date=format:'%Y%m%d_%H%M%S')

# NILを実行
java -jar /app/build/libs/NIL-all.jar \
  -s /app/Repos/pandas \
  -l py \
  -ch "$COMMIT_HASH" \
  -ct "$COMMIT_TIME" \
  -o "/app/results/pandas_${COMMIT_TIME}_${COMMIT_HASH:0:8}.csv"

exit
```

### 5. 大規模プロジェクトの最適化実行

```bash
docker-compose exec nil bash

# メモリとスレッドを最適化して実行
java -Xmx16g -XX:+UseG1GC -jar ./build/libs/NIL-all.jar \
  -s /app/Repos/large-project \
  -p 135 \
  -t 16 \
  -f 15 \
  -v 80 \
  -o /app/results/large_project_clones.csv

exit
```

---

## docker-compose.yml の詳細

### デフォルト設定

```yaml
services:
  nil:
    build: .
    volumes:
      - .:/app
    working_dir: /app
```

### カスタマイズ例

より実用的な設定：

```yaml
services:
  nil:
    build: .
    container_name: nil-detector
    volumes:
      - .:/app
      - ./Repos:/app/Repos # リポジトリディレクトリ
      - ./results:/app/results # 結果ディレクトリ
    working_dir: /app
    environment:
      - JAVA_OPTS=-Xmx16g -XX:+UseG1GC
    # リソース制限（必要に応じて）
    deploy:
      resources:
        limits:
          cpus: "16"
          memory: 32G
        reservations:
          cpus: "8"
          memory: 16G
    # 自動再起動
    restart: unless-stopped
```

---

## Dockerfile の詳細

### 現在の構成

```dockerfile
FROM openjdk:21-jdk-slim

# Install git and other necessary tools
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

CMD ["bash"]
```

### カスタマイズ例

#### 1. NIL を自動ビルド

```dockerfile
FROM openjdk:21-jdk-slim

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# NILを自動ビルド
RUN ./gradlew shadowJar

CMD ["bash"]
```

#### 2. 実行専用イメージ（マルチステージビルド）

```dockerfile
# ビルドステージ
FROM openjdk:21-jdk-slim AS builder

WORKDIR /build
COPY . .
RUN ./gradlew shadowJar

# 実行ステージ
FROM openjdk:21-jre-slim

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/build/libs/NIL-all.jar /app/NIL-all.jar

ENTRYPOINT ["java", "-jar", "/app/NIL-all.jar"]
```

---

## ボリュームマウント

### 推奨ディレクトリ構造

```
NIL/                        # ホストマシン
├── Repos/                  # 解析対象リポジトリ
│   ├── project1/
│   ├── project2/
│   └── ...
├── results/                # 結果出力先
│   ├── project1_clones.csv
│   └── ...
├── code_blocks/            # 中間ファイル（自動生成）
└── ...

↓ マウント先（コンテナ内）

/app/                       # コンテナ内
├── Repos/
├── results/
├── code_blocks/
└── ...
```

### マウントオプション

#### 読み取り専用マウント

解析対象を保護：

```yaml
volumes:
  - ./Repos:/app/Repos:ro # 読み取り専用
  - ./results:/app/results # 書き込み可能
```

#### パフォーマンス最適化（macOS）

```yaml
volumes:
  - .:/app:delegated # 書き込みパフォーマンス向上
  - ./Repos:/app/Repos:cached # 読み取りパフォーマンス向上
```

---

## トラブルシューティング

### 問題 1: パーミッションエラー

**症状:**

```
Permission denied: '/app/results/output.csv'
```

**解決方法:**

```bash
# ホストマシンで権限を変更
chmod -R 777 results/

# または、コンテナ内でユーザーIDを合わせる
docker-compose exec --user $(id -u):$(id -g) nil bash
```

### 問題 2: メモリ不足

**症状:**

```
java.lang.OutOfMemoryError: Java heap space
```

**解決方法:**

```bash
# JVMヒープサイズを増やす
docker-compose exec nil java -Xmx16g -jar ./build/libs/NIL-all.jar -s /app/Repos/project

# docker-compose.ymlで環境変数を設定
environment:
  - JAVA_OPTS=-Xmx16g
```

### 問題 3: コンテナが起動しない

**症状:**

```
ERROR: Cannot start service nil: ...
```

**解決方法:**

```bash
# ログを確認
docker-compose logs nil

# イメージを再ビルド
docker-compose build --no-cache

# 古いコンテナを削除
docker-compose down -v
docker-compose up -d
```

### 問題 4: ビルドが遅い

**症状:**
Gradle ビルドに時間がかかる

**解決方法:**

```bash
# Gradleキャッシュをマウント
# docker-compose.ymlに追加
volumes:
  - ~/.gradle:/root/.gradle  # Gradleキャッシュ
```

### 問題 5: Git クローンが失敗

**症状:**

```
fatal: could not create work tree dir 'repository': Permission denied
```

**解決方法:**

```bash
# コンテナ内で適切な権限のディレクトリにクローン
docker-compose exec nil bash
mkdir -p /app/Repos
cd /app/Repos
git clone https://github.com/username/repository.git
```

---

## パフォーマンス最適化

### 1. Docker リソース割り当て

Docker Desktop の設定で以下を調整：

- **CPU**: 物理コア数の 80-90%
- **メモリ**: システムメモリの 50-70%
- **Swap**: メモリと同等以上

### 2. ビルドキャッシュの活用

```bash
# .dockerignoreを作成
cat > .dockerignore << EOF
.git
.gradle
build
results
Repos
*.csv
*.log
EOF
```

### 3. レイヤーキャッシュの最適化

Dockerfile の最適化：

```dockerfile
FROM openjdk:21-jdk-slim

# 依存関係のインストール（変更が少ない）
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Gradleファイルを先にコピー（依存関係のキャッシュ）
COPY build.gradle.kts settings.gradle.kts gradlew ./
COPY gradle/ ./gradle/

# 依存関係のダウンロード
RUN ./gradlew dependencies --no-daemon || true

# ソースコードをコピー
COPY src/ ./src/

# ビルド
RUN ./gradlew shadowJar --no-daemon

CMD ["bash"]
```

---

## セキュリティ考慮事項

### 1. 非 root ユーザーでの実行

```dockerfile
FROM openjdk:21-jdk-slim

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 非rootユーザーを作成
RUN useradd -m -u 1000 niluser

WORKDIR /app
COPY --chown=niluser:niluser . .

USER niluser

CMD ["bash"]
```

### 2. 読み取り専用ルートファイルシステム

```yaml
services:
  nil:
    build: .
    read_only: true
    tmpfs:
      - /tmp
      - /app/build
```

---

## CI/CD 統合

### GitHub Actions での使用例

```yaml
name: NIL Clone Detection

on:
  push:
    branches: [main]

jobs:
  clone-detection:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout NIL
        uses: actions/checkout@v3
        with:
          repository: kusumotolab/NIL
          path: NIL

      - name: Checkout target repository
        uses: actions/checkout@v3
        with:
          path: target

      - name: Run NIL
        run: |
          cd NIL
          docker-compose up -d
          docker-compose exec -T nil ./gradlew shadowJar
          docker-compose exec -T nil java -jar ./build/libs/NIL-all.jar \
            -s /app/target \
            -o /app/results/clones.csv

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: clone-detection-results
          path: NIL/results/clones.csv
```

---

## まとめ

Docker を使用することで、以下のメリットがあります：

- **環境の一貫性**: どのマシンでも同じ環境で実行可能
- **依存関係の管理**: JDK 等の依存関係をコンテナに封じ込め
- **クリーンな実行環境**: ホストマシンを汚さない
- **再現性**: 同じ結果を保証

詳細な使用方法については、[使用ガイド](./NIL_USAGE_GUIDE.md)も参照してください。
