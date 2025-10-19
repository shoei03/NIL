# pair_diff.py - ペア差分分析ツール

## 概要

スナップショット間のメソッドペアの変化（追加・削除・維持）を分析するツール。

## 機能

- 複数のスナップショットから`clone_pairs.csv`を収集
- 隣接するスナップショット間でペアの差分を計算
- サマリーCSVと詳細リスト（オプション）を出力

## 使い方

### 基本実行（デフォルト値使用）

```bash
docker compose run --rm analysis python pair_diff.py
```

### オプション指定

```bash
docker compose run --rm analysis python pair_diff.py \
  -i /workspace/results \
  -o /app/output/pair_diff \
  --log-dir /app/logs \
  --no-emit-lists
```

## コマンドライン引数

| オプション | デフォルト値 | 説明 |
|-----------|-------------|------|
| `-i, --input-dir` | `/workspace/results` | スナップショットディレクトリ |
| `-o, --output-dir` | `/app/output/pair_diff_with_lists` | 出力ディレクトリ |
| `--log-dir` | `/app/logs` | ログ出力ディレクトリ |
| `--emit-lists` | `True` | 詳細リストを出力 |
| `--no-emit-lists` | - | 詳細リスト出力を無効化 |

## 入力形式

### ディレクトリ構造

```
input_dir/
├── 20240101_120000_abc123/
│   └── clone_pairs.csv
├── 20240102_130000_def456/
│   └── clone_pairs.csv
└── 20240103_140000_ghi789/
    └── clone_pairs.csv
```

### clone_pairs.csv 形式

```csv
method_a,method_b,ngram_similarity,lcs_similarity
path1:method1:args:ret,path2:method2:args:ret,0.95,0.90
...
```

## 出力

### 1. サマリーCSV

`pair_diff_summary.csv` - スナップショット間の変化統計

| カラム | 説明 |
|--------|------|
| snapshot_t | 前スナップショット名 |
| snapshot_t1 | 現スナップショット名 |
| added_count | 追加されたペア数 |
| deleted_count | 削除されたペア数 |
| persisted_count | 維持されたペア数 |
| total | 合計 |
| added_rate | 追加率 |
| deleted_rate | 削除率 |
| persisted_rate | 維持率 |

### 2. 詳細リスト（`--emit-lists`時）

各遷移ごとにディレクトリが作成され、以下のファイルが生成される：

```
output_dir/
├── pair_diff_summary.csv
└── 20240101_120000_abc123_to_20240102_130000_def456/
    ├── added.csv      # 追加されたペア
    ├── deleted.csv    # 削除されたペア
    └── persisted.csv  # 維持されたペア
```

各CSVの形式：

```csv
method_a,method_b
path1:method1:args:ret,path2:method2:args:ret
...
```

## ログ

- デフォルト: `/app/logs/pair_diff_YYYYMMDD_HHMMSS.log`
- コンソールとファイルの両方に出力
- 処理状況、エラー、統計情報を記録

## 処理フロー

1. スナップショットディレクトリを収集・ソート（ディレクトリ名の辞書順）
2. 各`clone_pairs.csv`を解析してペアセットを構築
3. 隣接するスナップショット間で差分計算：
   - **追加**: `current - previous`
   - **削除**: `previous - current`
   - **維持**: `previous ∩ current`
4. サマリーCSVに統計を出力
5. （オプション）詳細リストを出力

## エラーハンドリング

- 入力ディレクトリが存在しない → 終了コード 1
- CSV解析エラー → 警告ログ、処理継続
- その他の例外 → エラーログ、スタックトレース出力、終了コード 1
- Ctrl+C → 終了コード 130

## 注意事項

- スナップショットが2つ未満の場合は処理をスキップ
- ディレクトリ名は `YYYYMMDD_HHMMSS_*` 形式を推奨（辞書順ソートのため）
- ペアは無向（method_a < method_b に正規化）
- 空行や不正な行は警告ログを出力してスキップ