# method_tracking_details.csv の読み方

## ファイル構造

この CSV ファイルは、スナップショット間のメソッドレベルの変更を詳細に記録しています。

### カラム説明

| カラム名        | 説明                                               | 例                                       |
| --------------- | -------------------------------------------------- | ---------------------------------------- |
| `snapshot_t`    | 変更前のスナップショット（コミットハッシュ短縮形） | `87a3370b`                               |
| `snapshot_t1`   | 変更後のスナップショット（コミットハッシュ短縮形） | `71b65ab6`                               |
| `change_type`   | 変更の種類（下記参照）                             | `renamed`, `moved`, `added`              |
| `file_path`     | ファイルパス                                       | `/app/Repos/pandas/pandas/core/frame.py` |
| `method_name`   | メソッド名                                         | `groupby`                                |
| `signature`     | メソッドシグネチャ                                 | `groupby:self:Any;by:Any;axis:Any`       |
| `line_range_t`  | 変更前の行範囲                                     | `83-122`                                 |
| `line_range_t1` | 変更後の行範囲                                     | `93-135`                                 |
| `commit_t`      | 変更前のコミットハッシュ                           | `87a3370b`                               |
| `commit_t1`     | 変更後のコミットハッシュ                           | `71b65ab6`                               |
| `similarity`    | LCS 類似度（0.0-1.0）                              | `0.960` (96%)                            |

## 変更タイプ (change_type)

### 1. `exact` - 完全一致

ファイルパス、メソッド名、シグネチャがすべて同じで、実装も変更されていない。

**例:**

```
snapshot_t: 87a3370b → 71b65ab6
ファイル: bench/serialize.py
メソッド: roundtrip_archive
行範囲: 15-55 → 15-55
類似度: 100%
```

**意味**: このメソッドは 2 つのスナップショット間で全く変更されていない。

---

### 2. `token_hash` - トークンハッシュ一致

実装（トークン列）は全く同じだが、ファイル名やメソッド名が異なる可能性がある。

**例:**

```
snapshot_t: 87a3370b → 71b65ab6
ファイル: pandas/tests/test_libsparse.py
メソッド: check_cases
行範囲: 51-66 → 51-66
類似度: 100%
```

**意味**: 同じコードが別の場所にコピーされた、または名前が変更されたが実装は同じ。

---

### 3. `renamed` - リネーム

同じファイル内で、メソッド名が変更されたが実装は類似している（LCS 類似度 ≥ 90%）。

**例:**

```
snapshot_t: 87a3370b → 71b65ab6
ファイル: pandas/core/reshape.py
メソッド: get_new_values
行範囲: 130-155 → 134-160
類似度: 94%
```

**意味**: メソッド名が変更されたが、実装はほぼ同じ。

---

### 4. `moved` - ファイル移動

異なるファイルに移動したが、実装は類似している（LCS 類似度 ≥ 90%）。

**例:**

```
snapshot_t: 87a3370b → 71b65ab6
ファイル: pandas/core/internals.py
メソッド: _maybe_upcast_blocks
行範囲: 1010-1031 → 612-631
類似度: 97%
```

**意味**: メソッドが別のファイルに移動したが、実装はほぼ同じ。

---

### 5. `signature_changed` - シグネチャ変更

同じファイル、同じメソッド名だが、引数が変更された。

**例:**

```
snapshot_t: 87a3370b → 71b65ab6
ファイル: pandas/core/generic.py
メソッド: groupby
シグネチャ (t):  groupby:self:Any;by:Any;axis:Any;level:Any;as_index:Any
シグネチャ (t1): groupby:self:Any;by:Any;axis:Any;level:Any;as_index:Any;sort:Any
行範囲: 83-122 → 93-135
類似度: 96%
```

**意味**: 引数が追加・削除・変更されたが、メソッドの実装は類似している。

---

### 6. `refactored` - リファクタリング

実装が中程度に変更された（LCS 類似度 70% ≤ similarity < 90%）。

**例:**

```
snapshot_t: 87a3370b → 71b65ab6
ファイル: pandas/core/internals.py
メソッド: reindex_items
行範囲: 582-619 → 779-788
類似度: 81%
```

**意味**: メソッドの実装が部分的に書き換えられたが、まだ類似性がある。

---

### 7. `added` - 追加

新しいスナップショットで追加されたメソッド。

**例:**

```
snapshot_t: 9d008057 → 87a3370b
ファイル: pandas/core/groupby.py
メソッド: _is_indexed_like
行範囲 (t1): 462-477
```

**意味**: このメソッドは新しく追加された（前のスナップショットには存在しない）。

---

### 8. `deleted` - 削除

古いスナップショットから削除されたメソッド。

**例:**

```
snapshot_t: 87a3370b → 71b65ab6
ファイル: pandas/core/series.py
メソッド: _set_index
行範囲 (t): 202-213
```

**意味**: このメソッドは削除された（新しいスナップショットには存在しない）。

---

## 実用的な使い方

### 1. 特定のメソッドの変遷を追跡

```bash
# groupbyメソッドの変更履歴を見る
grep ",groupby," method_tracking_details.csv
```

### 2. リファクタリングされたメソッドを探す

```bash
# リファクタリングされたメソッドのみ抽出
grep ",refactored," method_tracking_details.csv
```

### 3. 大規模な変更を見つける

```bash
# 類似度が低い変更（大きなリファクタリング）を見つける
# Pythonスクリプトで類似度 < 0.8 のものを抽出
python -c "
import csv
with open('method_tracking_details.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['similarity'] and float(row['similarity']) < 0.8:
            print(f\"{row['method_name']} ({row['file_path']}): {row['similarity']}\")
"
```

### 4. ファイル移動を追跡

```bash
# moved タイプの変更を確認
grep ",moved," method_tracking_details.csv
```

## データ分析例

### Python での分析

```python
import pandas as pd

# CSVを読み込む
df = pd.read_csv('method_tracking_details.csv')

# 変更タイプごとの集計
print(df['change_type'].value_counts())

# 類似度の分布（refactoredのみ）
refactored = df[df['change_type'] == 'refactored']
print(refactored['similarity'].describe())

# 特定のファイルの変更履歴
frame_changes = df[df['file_path'].str.contains('frame.py')]
print(frame_changes[['method_name', 'change_type', 'similarity']])
```

## 注意事項

1. **空の値**: `added`メソッドは`line_range_t`が空、`deleted`メソッドは`line_range_t1`が空になります。

2. **類似度**: `exact`と`token_hash`は常に 1.000（100%）です。他のタイプは 0.7-1.0 の範囲。

3. **行番号**: 行範囲は Python ファイルの物理的な行番号です（1-indexed）。

4. **シグネチャ形式**: `method_name:param1:Type1;param2:Type2:ReturnType`

## 関連ファイル

- `method_tracking_summary.csv`: スナップショット間の変更サマリー
- `METHOD_TRACKING.md`: メソッド追跡機能の全体説明
