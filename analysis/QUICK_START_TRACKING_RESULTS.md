# Method Tracking Results - クイックスタート

## 📊 データ概要

このディレクトリには、pandas プロジェクトのメソッド追跡結果が含まれています。

### ファイル構成

```
output/
├── phase2_tracking/
│   ├── method_tracking_summary.csv    # スナップショット間の変更サマリー
│   └── method_tracking_details.csv    # メソッド単位の詳細な変更記録
└── ...
```

## 🎯 3 分でわかる！各ファイルの読み方

### 1. `method_tracking_summary.csv` - 全体像を把握

**用途**: 各スナップショット間の変更を一覧で確認

**サンプル**:

```csv
snapshot_t,snapshot_t1,exact_matches,token_hash_matches,renamed,moved,signature_changed,refactored,added_methods,deleted_methods,total_t,total_t1
87a3370b,71b65ab6,980,99,8,48,28,11,779,196,1370,1953
```

**読み方**:

- `87a3370b → 71b65ab6` のスナップショット間で:
  - 980 個のメソッドが完全に同じ (exact_matches)
  - 99 個のメソッドが実装は同じだが名前や場所が違う (token_hash_matches)
  - 8 個がリネーム、48 個がファイル移動、28 個がシグネチャ変更
  - 779 個が新規追加、196 個が削除

### 2. `method_tracking_details.csv` - 詳細を調査

**用途**: 個別のメソッドの変更を詳しく調べる

**サンプル**:

```csv
snapshot_t,snapshot_t1,change_type,file_path,method_name,signature,line_range_t,line_range_t1,similarity
87a3370b,71b65ab6,renamed,pandas/core/reshape.py,get_new_values,get_new_values:self:Any:None,130-155,134-160,0.940
```

**読み方**:

- `pandas/core/reshape.py`の`get_new_values`メソッドが
- 130-155 行から 134-160 行に移動し
- 類似度 94%でリネームされた

## 📈 変更タイプの意味

| タイプ              | 説明             | 類似度 | 例                           |
| ------------------- | ---------------- | ------ | ---------------------------- |
| `exact`             | 完全一致         | 100%   | コードが全く変更されていない |
| `token_hash`        | 実装が同一       | 100%   | 同じコードが別の場所にコピー |
| `renamed`           | リネーム         | ≥90%   | `old_name` → `new_name`      |
| `moved`             | ファイル移動     | ≥90%   | `file1.py` → `file2.py`      |
| `signature_changed` | 引数変更         | 変動   | 引数が追加・削除された       |
| `refactored`        | リファクタリング | 70-90% | 実装が部分的に変更           |
| `added`             | 新規追加         | -      | 新しく作成されたメソッド     |
| `deleted`           | 削除             | -      | 削除されたメソッド           |

## 🔍 よくある使い方

### 1. 特定メソッドの変遷を追跡

```bash
# groupbyメソッドの履歴
grep ",groupby," method_tracking_details.csv
```

### 2. 大きな変更があったファイルを探す

```python
import pandas as pd

df = pd.read_csv('method_tracking_details.csv')

# ファイルごとの変更数
file_changes = df['file_path'].value_counts()
print(file_changes.head(10))
```

### 3. リファクタリングを分析

```python
# リファクタリングされたメソッドの類似度分布
refactored = df[df['change_type'] == 'refactored']
print(refactored['similarity'].describe())
```

## 📊 このデータセットの統計

### 全体の数値（例: phase2_tracking）

- **総レコード数**: 32,470 件
- **スナップショット数**: 9 ペア（10 スナップショット）
- **期間**: 2009 年 〜 2014 年

### 変更タイプの内訳

```
exact:              23,437件 (72.1%) - ほとんどのメソッドは変更されない
added:               6,964件 (21.4%) - 新規メソッドが多い
deleted:             1,109件 (3.4%)
signature_changed:     435件 (1.3%)
token_hash:            189件 (0.6%)
moved:                 157件 (0.5%)
refactored:            114件 (0.4%)
renamed:                65件 (0.2%)
```

### 最も変更が多いファイル

1. `pandas/tests/test_frame.py` - 2,667 変更
2. `pandas/tests/test_series.py` - 1,581 変更
3. `pandas/tests/test_groupby.py` - 1,203 変更
4. `pandas/core/frame.py` - 1,051 変更
5. `pandas/tests/test_multilevel.py` - 870 変更

## 💡 実用例

### ケース 1: API の安定性分析

「どのメソッドが頻繁に変更されているか？」

```python
import pandas as pd
df = pd.read_csv('method_tracking_details.csv')

# 同じメソッド名で複数回変更されているものを探す
method_changes = df.groupby('method_name').size().sort_values(ascending=False)
print(method_changes.head(10))

# 結果例:
# __init__    637回  ← コンストラクタは頻繁に変更される
# setUp       224回  ← テストのセットアップも多い
# __getitem__ 109回  ← 配列アクセスの実装は複雑
```

**発見**: `__init__`や`__getitem__`などの特殊メソッドは頻繁に変更される。これらは複雑な機能を持つため、何度も改善されている。

### ケース 2: 大規模リファクタリングの検出

「コードが大幅に書き換えられた箇所は？」

```python
# 類似度が低い変更（大きな書き換え）を探す
df['similarity'] = pd.to_numeric(df['similarity'], errors='coerce')
big_changes = df[(df['similarity'] < 0.75) & (df['similarity'].notna())]

print(f"大規模リファクタリング: {len(big_changes)}件")
for _, row in big_changes.iterrows():
    print(f"{row['method_name']} in {row['file_path']}: {row['similarity']:.1%}")

# 結果例:
# _sanitize_column in pandas/core/frame.py: 72%
# xs in pandas/core/frame.py: 70%
```

**発見**: 24 件の大規模リファクタリングが検出された。これらは実装が大幅に変更されたメソッド。

### ケース 3: ファイル移動の追跡

「コードの再構成でどのメソッドが移動したか？」

```python
moved = df[df['change_type'] == 'moved']
print(f"ファイル間を移動したメソッド: {len(moved)}個")

# よく移動するメソッドを探す
moved_methods = moved.groupby('method_name').size().sort_values(ascending=False)
print(moved_methods[moved_methods > 1])

# 結果例:
# __init__         4回移動  ← クラスがファイル間で移動
# _arith_method    3回移動  ← 算術演算のヘルパー
```

**発見**: 157 個のメソッドがファイル間を移動。コードベースの再構成が行われた証拠。

### ケース 4: テストコードの進化

「テストコードとプロダクションコードの変更比率は？」

```python
test_files = df[df['file_path'].str.contains('/tests/')]
prod_files = df[~df['file_path'].str.contains('/tests/')]

print(f"テスト: {len(test_files)} ({len(test_files)/len(df)*100:.1f}%)")
print(f"本体: {len(prod_files)} ({len(prod_files)/len(df)*100:.1f}%)")

# 結果例:
# テスト: 18,654件 (57.4%)
# 本体:   13,816件 (42.6%)
```

**発見**: 変更の半分以上がテストコード。テストが充実していることを示す。

### ケース 5: API 変更の影響範囲

「シグネチャが変更されたメソッド（API の非互換変更）は？」

```python
sig_changed = df[df['change_type'] == 'signature_changed']
files_affected = sig_changed.groupby('file_path').size().sort_values(ascending=False)

print(f"シグネチャ変更: {len(sig_changed)}件")
print("最も影響を受けたファイル:")
print(files_affected.head(5))

# 結果例:
# pandas/core/frame.py      79件  ← DataFrameのAPIが多く変更
# pandas/core/internals.py  34件
```

**発見**: 435 個のメソッドでシグネチャが変更。API の後方互換性に注意が必要。

## 📚 詳細ドキュメント

より詳しい情報は以下を参照：

- [HOW_TO_READ_TRACKING_RESULTS.md](./HOW_TO_READ_TRACKING_RESULTS.md) - 各カラムと change_type の詳細説明
- [README.md](./README.md) - 分析スクリプトの使い方
- [../METHOD_TRACKING.md](../METHOD_TRACKING.md) - 機能の全体像と実装詳細

## 🚀 次のステップ

1. **データを見てみる**: `head method_tracking_details.csv`
2. **統計を取る**: Python/R でデータ分析
3. **可視化する**: 変更の時系列グラフを作成
4. **パターンを探す**: 頻繁に変更されるメソッドを特定

---

**Tips**: CSV ファイルは大きいので、Visual Studio Code の[Rainbow CSV](https://marketplace.visualstudio.com/items?itemName=mechatroner.rainbow-csv)拡張機能を使うと見やすくなります！
