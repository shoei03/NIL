# Method Evolution Tracker ドキュメント

## 概要

Javaメソッドのスナップショット間の変更を追跡し、リファクタリング操作を検出するツールです。

## 主な機能

- **完全一致検出**: ファイルパス・シグネチャが同一のメソッド
- **トークンハッシュ一致**: 実装が同じだが位置/シグネチャが変更されたメソッド
- **類似度ベース検出** (オプション):
  - `renamed`: メソッド名変更 (同ファイル内、類似度≥90%)
  - `moved`: ファイル移動 (別ファイルへ、類似度≥90%)
  - `signature_changed`: シグネチャ変更 (同ファイル、同メソッド名)
  - `refactored`: その他のリファクタリング
- **追加/削除検出**: 新規メソッドと削除されたメソッド

## 実行方法

### 基本実行（デフォルト設定）

```bash
# Dockerコンテナ内
docker compose run --rm analysis python method_tracker.py

# または直接実行
python method_tracker.py
```

### デフォルト設定

- 入力: `/workspace/results/`
- 出力: `/app/output/pair_diff_with_lists/`
- 類似度マッチング: **有効**
- N-gram閾値: `10.0` (10%)
- LCS閾値: `70.0` (70%)

### カスタマイズ実行

```bash
# 入力ディレクトリを変更
python method_tracker.py -i /path/to/snapshots -o /path/to/output

# 類似度マッチングを無効化
python method_tracker.py --no-similarity

# 閾値を調整
python method_tracker.py --ngram-threshold 15 --lcs-threshold 80

# ログファイルを指定
python method_tracker.py --log /path/to/logfile.log
```

## 入力形式

### ディレクトリ構造

```
/workspace/results/
├── YYYYMMDD_HHMMSS_commithash1/
│   └── code_blocks.csv
├── YYYYMMDD_HHMMSS_commithash2/
│   └── code_blocks.csv
└── YYYYMMDD_HHMMSS_commithash3/
    └── code_blocks.csv
```

### code_blocks.csv フォーマット

9列のCSV形式（ヘッダーなし）:

```
token_hash,file_path,start_line,end_line,method_name,return_type,parameters,commit_hash,token_sequence
abc123,com/example/Foo.java,10,20,myMethod,void,"String arg",def456,"1;2;3;4;5"
```

## 出力形式

### ディレクトリ構造

```
/app/output/pair_diff_with_lists/
├── method_tracking_summary.csv                           # 全体サマリー
├── YYYYMMDD_HHMMSS_commit1_to_YYYYMMDD_HHMMSS_commit2/
│   └── method_tracing.csv                                # 詳細データ
├── YYYYMMDD_HHMMSS_commit2_to_YYYYMMDD_HHMMSS_commit3/
│   └── method_tracing.csv
└── ...
```

### method_tracking_summary.csv

各ペア比較の統計サマリー:

```csv
snapshot_t,snapshot_t1,exact_matches,token_hash_matches,renamed,moved,signature_changed,refactored,added_methods,deleted_methods,total_t,total_t1
20241001_120000_abc123,20241001_130000_def456,150,20,5,3,2,10,15,8,200,207
```

**列の説明:**
- `snapshot_t/snapshot_t1`: 比較した2つのスナップショット
- `exact_matches`: 完全一致数
- `token_hash_matches`: トークンハッシュ一致数
- `renamed/moved/signature_changed/refactored`: 各リファクタリング操作の数
- `added_methods/deleted_methods`: 追加・削除されたメソッド数
- `total_t/total_t1`: 各スナップショットの総メソッド数

### method_tracing.csv

個別ペアの詳細データ:

```csv
change_type,method_t_token_hash,method_t1_token_hash,similarity
exact,abc123,abc123,1.000
token_hash,def456,def456,1.000
renamed,ghi789,ghi789,0.950
moved,jkl012,jkl012,0.920
signature_changed,mno345,mno345,0.880
refactored,pqr678,stu901,0.750
added,,vwx234,
deleted,yz012,,
```

**列の説明:**
- `change_type`: 変更タイプ (exact/token_hash/renamed/moved/signature_changed/refactored/added/deleted)
- `method_t_token_hash`: 前スナップショットのメソッドのトークンハッシュ
- `method_t1_token_hash`: 後スナップショットのメソッドのトークンハッシュ
- `similarity`: 類似度 (0.0〜1.0、added/deletedは空)

## パフォーマンス最適化

類似度マッチングは以下の手法で高速化されています:

1. **候補の絞り込み**: 同じファイルパス/メソッド名を優先的に比較
2. **2段階フィルタリング**: N-gram (高速) → LCS (精密)
3. **インデックス構築**: ファイルパス別・メソッド名別のインデックス活用

大規模プロジェクト (1000+ メソッド) でも実用的な速度で動作します。

## コマンドラインオプション

| オプション | デフォルト | 説明 |
|-----------|----------|------|
| `-i, --input-dir` | `/workspace/results/` | 入力ディレクトリ |
| `-o, --output-dir` | `/app/output/pair_diff_with_lists` | 出力ディレクトリ |
| `--input-file` | `code_blocks.csv` | 入力ファイル名 |
| `--log` | 自動生成 | ログファイルパス |
| `--no-similarity` | False | 類似度マッチング無効化 |
| `--ngram-threshold` | `10.0` | N-gram閾値 (%) |
| `--lcs-threshold` | `70.0` | LCS閾値 (%) |

## ログ出力

デフォルトで `logs/method_tracker_YYYYMMDD_HHMMSS.log` にログが記録されます。

```
2025-10-20 02:57:27 - INFO - Processing 36 code_blocks files
2025-10-20 02:57:27 - INFO - code_blocks.csv: 1234 methods extracted
2025-10-20 02:57:27 - INFO - Exact matches: 1150
2025-10-20 02:57:27 - INFO - Token hash matches: 45
2025-10-20 02:57:27 - INFO - Finding similarity matches: 39 x 52 comparisons
2025-10-20 02:57:28 - INFO - Found 15 similarity-based matches
```

## トラブルシューティング

### 処理が遅い場合

- `--no-similarity` で類似度マッチングを無効化
- `--ngram-threshold` を上げて厳格化 (例: `15` or `20`)

### メモリ不足の場合

- スナップショット数を減らす
- 類似度マッチングを無効化

### ログレベルを変更する場合

コード内の `logging.INFO` を `logging.DEBUG` に変更