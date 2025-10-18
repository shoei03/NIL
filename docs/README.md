# NIL ドキュメント

このディレクトリには、NIL（N-gram, Inverted index, LCS）クローン検出ツールに関する詳細なドキュメントが含まれています。

## ドキュメント一覧

### 1. [使用ガイド](./NIL_USAGE_GUIDE.md)

**対象読者**: NIL を使い始めるすべてのユーザー

**内容**:

- NIL の動作原理の説明
- Docker 実行方法（基本から応用まで）
- 入出力形式の概要
- 実行例とパフォーマンスチューニング
- トラブルシューティング

**こんな時に読む**:

- NIL を初めて使う
- 基本的な使い方を知りたい
- Docker で実行したい

### 2. [Docker 実行ガイド](./DOCKER_GUIDE.md)

**対象読者**: Docker を使って NIL を実行したいユーザー

**内容**:

- Docker イメージの詳細
- セットアップ手順（Docker Compose / Docker CLI）
- ユースケース別実行例
- docker-compose.yml と Dockerfile のカスタマイズ
- ボリュームマウントとパフォーマンス最適化
- CI/CD 統合

**こんな時に読む**:

- 環境構築を簡単にしたい
- 複数のプロジェクトを解析したい
- CI/CD パイプラインに組み込みたい
- コンテナ環境で開発している

### 3. [入出力フォーマット詳細](./IO_FORMAT.md)

**対象読者**: NIL の入出力仕様を詳しく知りたいユーザー

**内容**:

- すべてのコマンドライン引数の詳細
- 対応プログラミング言語の仕様
- 出力フォーマット（標準形式、BigCloneEval 形式）
- 類似度計算方法の数式
- 中間ファイルの説明
- 出力ファイルの解析方法

**こんな時に読む**:

- パラメータの詳細を知りたい
- 出力結果を詳しく理解したい
- 結果を他のツールと連携させたい
- カスタム解析を行いたい

### 4. [アーキテクチャドキュメント](./ARCHITECTURE.md)

**対象読者**: NIL の内部実装を理解したい開発者・研究者

**内容**:

- システムアーキテクチャ（3 層構造）
- コアコンポーネントの詳細
- 処理フローとアルゴリズム
- データ構造の設計
- 並列処理戦略
- 最適化技法
- 拡張方法

**こんな時に読む**:

- NIL の仕組みを深く理解したい
- 新しい機能を追加したい
- 新しい言語サポートを追加したい
- 研究で実装詳細が必要
- パフォーマンス改善を検討したい

## ドキュメントの読み方

### 初めて NIL を使う場合

1. **[使用ガイド](./NIL_USAGE_GUIDE.md)** を読む

   - 動作原理を理解
   - 基本的な実行方法を学ぶ

2. **[Docker 実行ガイド](./DOCKER_GUIDE.md)** を読む（Docker を使う場合）

   - セットアップ手順に従う
   - 実行例を試す

3. **[入出力フォーマット詳細](./IO_FORMAT.md)** を参照する（必要に応じて）
   - パラメータの詳細を確認
   - 出力結果の解釈

### 高度な使い方をしたい場合

1. **[使用ガイド](./NIL_USAGE_GUIDE.md)** のパフォーマンスチューニングセクション

   - パーティション数の最適化
   - スレッド数の調整
   - 閾値の設定

2. **[Docker 実行ガイド](./DOCKER_GUIDE.md)** のカスタマイズセクション

   - Dockerfile の最適化
   - リソース制限の設定

3. **[入出力フォーマット詳細](./IO_FORMAT.md)** の解析例
   - 結果の統計解析
   - Python スクリプトでの解析

### NIL を拡張したい場合

1. **[アーキテクチャドキュメント](./ARCHITECTURE.md)** を熟読

   - システム全体の理解
   - コンポーネントの関係性

2. **拡張性セクション** を確認

   - 新しい言語の追加方法
   - カスタム類似度メトリクスの実装

3. ソースコードを読む
   - `src/main/kotlin/jp/ac/osaka_u/sdl/nil/` 配下

## クイックリファレンス

### よく使うコマンド

```bash
# 基本的な実行
java -jar NIL-all.jar -s /path/to/source

# Pythonプロジェクトの解析
java -jar NIL-all.jar -s /path/to/python/project -l py

# Docker Composeでの実行
docker-compose up -d
docker-compose exec nil java -jar ./build/libs/NIL-all.jar -s /app/Repos/project

# 大規模プロジェクト（最適化）
java -Xmx16g -jar NIL-all.jar -s /path/to/large/project -p 135 -t 16
```

### パラメータのデフォルト値

| パラメータ                | デフォルト |
| ------------------------- | ---------- |
| 最小行数 (`-mil`)         | 6          |
| 最小トークン数 (`-mit`)   | 50         |
| N-gram (`-n`)             | 5          |
| パーティション数 (`-p`)   | 10         |
| フィルタリング閾値 (`-f`) | 10%        |
| 検証閾値 (`-v`)           | 70%        |
| スレッド数 (`-t`)         | 全スレッド |
| 言語 (`-l`)               | java       |

### 出力フォーマット

**標準形式**:

```csv
file_A,start_A,end_A,file_B,start_B,end_B,ngram_sim,lcs_sim
```

**BCE 形式** (`-bce`):

```csv
dir_A,file_A,start_A,end_A,dir_B,file_B,start_B,end_B,ngram_sim,lcs_sim
```

## トラブルシューティング

問題が発生した場合は、以下のドキュメントのトラブルシューティングセクションを参照してください：

- [使用ガイド - トラブルシューティング](./NIL_USAGE_GUIDE.md#トラブルシューティング)
- [Docker 実行ガイド - トラブルシューティング](./DOCKER_GUIDE.md#トラブルシューティング)
- [入出力フォーマット詳細 - トラブルシューティング](./IO_FORMAT.md#トラブルシューティング)

## 関連リソース

### プロジェクトルートのドキュメント

- [README.md](../README.md) - プロジェクト概要
- [INSTALL.md](../INSTALL.md) - インストール手順
- [EXPERIMENT.md](../EXPERIMENT.md) - 実験方法
- [METHOD_TRACKING.md](../METHOD_TRACKING.md) - メソッド追跡機能
- [REQUIREMENTS.md](../REQUIREMENTS.md) - 要件定義

### 学術論文

- FSE '21 論文: [camera-ready.pdf](../camera-ready.pdf)
- DOI: [10.5281/zenodo.4492665](https://doi.org/10.5281/zenodo.4492665)

### リポジトリ

- GitHub: [https://github.com/kusumotolab/NIL](https://github.com/kusumotolab/NIL)

## フィードバック

ドキュメントに関するフィードバックや改善提案は、GitHub の Issue までお願いします。

## ライセンス

このドキュメントは、NIL プロジェクトと同じライセンス（[LICENSE](../LICENSE)参照）の下で提供されています。

---

**最終更新**: 2025 年 10 月 16 日
