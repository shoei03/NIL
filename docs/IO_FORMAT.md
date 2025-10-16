# NIL 入出力フォーマット詳細

このドキュメントでは、NIL の入力仕様と出力フォーマットについて詳しく説明します。

## 目次

1. [入力仕様](#入力仕様)
2. [出力フォーマット](#出力フォーマット)
3. [中間ファイル](#中間ファイル)
4. [フォーマット変換](#フォーマット変換)
5. [実例とサンプル](#実例とサンプル)

---

## 入力仕様

### コマンドライン引数

#### 必須パラメータ

| パラメータ         | 短縮形 | 長い形式 | 説明                   | 例                    |
| ------------------ | ------ | -------- | ---------------------- | --------------------- |
| ソースディレクトリ | `-s`   | `--src`  | 解析対象のディレクトリ | `-s /path/to/project` |

#### オプションパラメータ - 検出設定

| パラメータ         | 短縮形 | 長い形式                   | デフォルト | 説明                                | 有効範囲 |
| ------------------ | ------ | -------------------------- | ---------- | ----------------------------------- | -------- |
| 最小行数           | `-mil` | `--min-line`               | 6          | クローンとみなす最小行数            | 1 以上   |
| 最小トークン数     | `-mit` | `--min-token`              | 50         | クローンとみなす最小トークン数      | 1 以上   |
| N-gram サイズ      | `-n`   | `--n-gram`                 | 5          | N-gram の N                         | 1 以上   |
| フィルタリング閾値 | `-f`   | `--filtration-threshold`   | 10         | 初期フィルタリングの類似度閾値（%） | 0-100    |
| 検証閾値           | `-v`   | `--verification-threshold` | 70         | 最終検証の類似度閾値（%）           | 0-100    |

#### オプションパラメータ - 実行設定

| パラメータ       | 短縮形 | 長い形式             | デフォルト | 説明                   |
| ---------------- | ------ | -------------------- | ---------- | ---------------------- |
| パーティション数 | `-p`   | `--partition-number` | 10         | データ分割数           |
| スレッド数       | `-t`   | `--threads`          | 全スレッド | 並列処理スレッド数     |
| 言語             | `-l`   | `--language`         | java       | 対象プログラミング言語 |

#### オプションパラメータ - 出力設定

| パラメータ        | 短縮形 | 長い形式                       | デフォルト               | 説明               |
| ----------------- | ------ | ------------------------------ | ------------------------ | ------------------ |
| 出力ファイル      | `-o`   | `--output`                     | `result_{n}_{f}_{v}.csv` | 結果ファイルのパス |
| BigCloneEval 形式 | `-bce` | `--bigcloneeval`               | false                    | BCE 互換形式で出力 |
| MIF 形式          | `-mif` | `--mutationinjectionframework` | false                    | MIF 互換モード     |

#### オプションパラメータ - 追跡機能

| パラメータ             | 短縮形 | 長い形式             | デフォルト | 説明                     |
| ---------------------- | ------ | -------------------- | ---------- | ------------------------ |
| コミットハッシュ       | `-ch`  | `--commit-hash`      | なし       | Git コミットハッシュ     |
| コミットタイムスタンプ | `-ct`  | `--commit-timestamp` | なし       | コミットのタイムスタンプ |

### 対応プログラミング言語

#### Java

**指定方法**: `-l java`

**対応ファイル**: `.java`

**例**:

```bash
java -jar NIL-all.jar -s /path/to/java/project -l java
```

#### C

**指定方法**: `-l c`

**対応ファイル**: `.c`, `.h`

**例**:

```bash
java -jar NIL-all.jar -s /path/to/c/project -l c
```

#### C++

**指定方法**: `-l cpp`

**対応ファイル**: `.cpp`, `.hpp`

**例**:

```bash
java -jar NIL-all.jar -s /path/to/cpp/project -l cpp
```

#### C#

**指定方法**: `-l cs` または `-l csharp`

**対応ファイル**: `.cs`

**例**:

```bash
java -jar NIL-all.jar -s /path/to/csharp/project -l cs
```

#### Python

**指定方法**: `-l py` または `-l python`

**対応ファイル**: `.py`

**例**:

```bash
java -jar NIL-all.jar -s /path/to/python/project -l py
```

#### Kotlin

**指定方法**: `-l kt` または `-l kotlin`

**対応ファイル**: `.kt`

**例**:

```bash
java -jar NIL-all.jar -s /path/to/kotlin/project -l kt
```

---

## 出力フォーマット

### 標準出力形式

デフォルト（`-bce` なし）の出力形式です。

#### フォーマット

```csv
file_path_A,start_line_A,end_line_A,file_path_B,start_line_B,end_line_B,ngram_similarity,lcs_similarity
```

#### フィールド詳細

| フィールド         | 型           | 説明                                       | 例                         |
| ------------------ | ------------ | ------------------------------------------ | -------------------------- |
| `file_path_A`      | String       | 1 つ目のクローンのファイルパス（絶対パス） | `/project/src/Main.java`   |
| `start_line_A`     | Integer      | 1 つ目のクローンの開始行番号               | `10`                       |
| `end_line_A`       | Integer      | 1 つ目のクローンの終了行番号               | `25`                       |
| `file_path_B`      | String       | 2 つ目のクローンのファイルパス（絶対パス） | `/project/src/Helper.java` |
| `start_line_B`     | Integer      | 2 つ目のクローンの開始行番号               | `50`                       |
| `end_line_B`       | Integer      | 2 つ目のクローンの終了行番号               | `65`                       |
| `ngram_similarity` | Double       | N-gram ベース類似度（%）                   | `85.5`                     |
| `lcs_similarity`   | Double/Empty | LCS ベース類似度（%）※                     | `78.2`                     |

※ LCS 検証が実行された場合のみ出力（検証閾値を超えた場合）

#### サンプル出力

```csv
/Users/user/project/src/main/java/Main.java,10,25,/Users/user/project/src/main/java/Helper.java,50,65,85.5,78.2
/Users/user/project/src/main/java/Utils.java,100,120,/Users/user/project/src/main/java/Common.java,30,50,92.3,88.7
/Users/user/project/src/main/java/Parser.java,200,230,/Users/user/project/src/main/java/Lexer.java,150,180,75.8,72.1
```

### BigCloneEval 互換形式

`-bce` オプション使用時の出力形式です。BigCloneEval ベンチマークとの互換性があります。

#### フォーマット

```csv
dir_A,file_A,start_line_A,end_line_A,dir_B,file_B,start_line_B,end_line_B,ngram_similarity,lcs_similarity
```

#### フィールド詳細

| フィールド         | 型           | 説明                               | 例                        |
| ------------------ | ------------ | ---------------------------------- | ------------------------- |
| `dir_A`            | String       | 1 つ目のクローンのディレクトリパス | `/project/src/main/java/` |
| `file_A`           | String       | 1 つ目のクローンのファイル名       | `Main.java`               |
| `start_line_A`     | Integer      | 1 つ目のクローンの開始行番号       | `10`                      |
| `end_line_A`       | Integer      | 1 つ目のクローンの終了行番号       | `25`                      |
| `dir_B`            | String       | 2 つ目のクローンのディレクトリパス | `/project/src/main/java/` |
| `file_B`           | String       | 2 つ目のクローンのファイル名       | `Helper.java`             |
| `start_line_B`     | Integer      | 2 つ目のクローンの開始行番号       | `50`                      |
| `end_line_B`       | Integer      | 2 つ目のクローンの終了行番号       | `65`                      |
| `ngram_similarity` | Double       | N-gram ベース類似度（%）           | `85.5`                    |
| `lcs_similarity`   | Double/Empty | LCS ベース類似度（%）              | `78.2`                    |

#### サンプル出力

```csv
/Users/user/project/src/main/java/,Main.java,10,25,/Users/user/project/src/main/java/,Helper.java,50,65,85.5,78.2
/Users/user/project/src/main/java/,Utils.java,100,120,/Users/user/project/src/main/java/,Common.java,30,50,92.3,88.7
```

### 類似度の計算方法

#### N-gram 類似度

```
ngram_similarity = (共通N-gram数 × 2) / (A のN-gram総数 + B のN-gram総数) × 100
```

**例**:

- コード A: 100 個の N-gram
- コード B: 120 個の N-gram
- 共通 N-gram: 80 個

```
ngram_similarity = (80 × 2) / (100 + 120) × 100 = 72.73%
```

#### LCS 類似度

```
lcs_similarity = (LCS長 × 2) / (A のトークン数 + B のトークン数) × 100
```

**例**:

- コード A: 150 トークン
- コード B: 180 トークン
- LCS 長: 120 トークン

```
lcs_similarity = (120 × 2) / (150 + 180) × 100 = 72.73%
```

---

## 中間ファイル

NIL は実行中に以下の中間ファイルを生成します。

### clone_pairs ファイル

**場所**: プロジェクトルート

**形式**:

```csv
id_A,id_B,ngram_similarity,lcs_similarity
```

**説明**:

- TokenSequence の ID ベースで保存
- フォーマット変換前の生データ

**例**:

```csv
0,15,85.5,78.2
2,42,92.3,88.7
10,33,75.8,
```

### code_blocks ファイル

**場所**: `code_blocks/` ディレクトリ

**命名規則**: `code_blocks_<timestamp>_<commit_hash>`

**例**: `code_blocks_20240101_120000_a1b2c3d4`

**形式**: バイナリ形式（内部使用）

**内容**:

- TokenSequence の詳細情報
- ファイルパス
- 行番号範囲
- トークンデータ

---

## フォーマット変換

### 標準形式への変換

`clone_pairs` から最終出力への変換プロセス：

```
clone_pairs
  ↓
TokenSequence情報を読み込み
  ↓
ID → ファイルパス変換
  ↓
標準CSV出力
```

### BigCloneEval 形式への変換

追加の処理：

```
標準形式
  ↓
ファイルパスを分割
  ├─ ディレクトリパス
  └─ ファイル名
  ↓
BCE形式CSV出力
```

### 実装コード抜粋

```kotlin
// 標準形式（CSV）
class CSV : Format {
    override fun convert(outputFileName: String, ...) {
        val clonePairs = readClonePairs()
        val tokenSequences = readCodeBlocks()

        File(outputFileName).bufferedWriter().use { bw ->
            clonePairs.forEach { pair ->
                val ts1 = tokenSequences[pair.id1]
                val ts2 = tokenSequences[pair.id2]

                bw.appendLine(
                    "${ts1.filePath},${ts1.startLine},${ts1.endLine}," +
                    "${ts2.filePath},${ts2.startLine},${ts2.endLine}," +
                    "${pair.nGramSimilarity},${pair.lcsSimilarity}"
                )
            }
        }
    }
}

// BigCloneEval形式
class BCEFormat : Format {
    override fun convert(outputFileName: String, ...) {
        val clonePairs = readClonePairs()
        val tokenSequences = readCodeBlocks()

        File(outputFileName).bufferedWriter().use { bw ->
            clonePairs.forEach { pair ->
                val ts1 = tokenSequences[pair.id1]
                val ts2 = tokenSequences[pair.id2]

                val (dir1, file1) = splitPath(ts1.filePath)
                val (dir2, file2) = splitPath(ts2.filePath)

                bw.appendLine(
                    "$dir1,$file1,${ts1.startLine},${ts1.endLine}," +
                    "$dir2,$file2,${ts2.startLine},${ts2.endLine}," +
                    "${pair.nGramSimilarity},${pair.lcsSimilarity}"
                )
            }
        }
    }
}
```

---

## 実例とサンプル

### 例 1: Java プロジェクトのクローン検出

**コマンド**:

```bash
java -jar NIL-all.jar \
  -s /project/java-app \
  -mil 10 \
  -mit 100 \
  -f 15 \
  -v 80 \
  -o clones.csv
```

**出力ファイル**: `clones.csv`

**内容例**:

```csv
/project/java-app/src/main/java/com/example/Service.java,45,72,/project/java-app/src/main/java/com/example/Helper.java,120,147,95.3,91.2
/project/java-app/src/main/java/com/example/Util.java,200,235,/project/java-app/src/test/java/com/example/UtilTest.java,15,50,88.7,85.4
/project/java-app/src/main/java/com/example/Parser.java,300,340,/project/java-app/src/main/java/com/example/Lexer.java,80,120,82.5,79.8
```

**解釈**:

- 3 つのクローンペアが検出された
- 最初のペアは N-gram 類似度 95.3%、LCS 類似度 91.2%
- すべて検証閾値（80%）を超えている

### 例 2: Python プロジェクト（BCE 形式）

**コマンド**:

```bash
java -jar NIL-all.jar \
  -s /project/python-app \
  -l py \
  -bce \
  -o bce_clones.csv
```

**出力ファイル**: `bce_clones.csv`

**内容例**:

```csv
/project/python-app/src/,main.py,10,35,/project/python-app/src/,helper.py,50,75,87.5,83.2
/project/python-app/lib/,utils.py,100,140,/project/python-app/lib/,common.py,200,240,92.1,89.5
```

### 例 3: コミット追跡機能付き

**コマンド**:

```bash
java -jar NIL-all.jar \
  -s /project/repo \
  -ch a1b2c3d4e5f6 \
  -ct 20240101_120000 \
  -o results/clones_20240101_120000_a1b2c3d4.csv
```

**出力ファイル名**: `results/clones_20240101_120000_a1b2c3d4.csv`

**code_blocks ファイル名**: `code_blocks/code_blocks_20240101_120000_a1b2c3d4`

これにより、特定のコミット時点でのクローン情報を追跡できます。

### 例 4: 大規模プロジェクトの段階的解析

**第 1 段階**: 低い閾値で広範囲に検出

```bash
java -jar NIL-all.jar \
  -s /large-project \
  -f 5 \
  -v 50 \
  -p 135 \
  -o phase1_clones.csv
```

**第 2 段階**: 高い閾値で厳格に検出

```bash
java -jar NIL-all.jar \
  -s /large-project \
  -f 20 \
  -v 90 \
  -p 135 \
  -o phase2_clones.csv
```

**結果の比較**:

- `phase1_clones.csv`: より多くのクローン（偽陽性を含む可能性）
- `phase2_clones.csv`: 高品質なクローンのみ

---

## 出力ファイルの解析

### CSV ファイルの基本統計

```bash
# クローンペア数
wc -l result.csv

# 類似度の分布（N-gram）
cut -d',' -f7 result.csv | sort -n | uniq -c

# 類似度の分布（LCS）
cut -d',' -f8 result.csv | grep -v '^$' | sort -n | uniq -c

# 最も類似度の高いペア
sort -t',' -k7 -nr result.csv | head -10
```

### ファイル別クローン数

```bash
# ファイルAの頻度
cut -d',' -f1 result.csv | sort | uniq -c | sort -rn

# ファイルBの頻度
cut -d',' -f4 result.csv | sort | uniq -c | sort -rn
```

### Python での解析例

```python
import pandas as pd

# CSVを読み込み
df = pd.read_csv('result.csv',
                 header=None,
                 names=['file_a', 'start_a', 'end_a',
                        'file_b', 'start_b', 'end_b',
                        'ngram_sim', 'lcs_sim'])

# 基本統計
print(df.describe())

# 類似度でフィルタ
high_similarity = df[df['ngram_sim'] >= 90]
print(f"High similarity clones: {len(high_similarity)}")

# ファイル別統計
file_counts = pd.concat([
    df['file_a'].value_counts(),
    df['file_b'].value_counts()
]).groupby(level=0).sum().sort_values(ascending=False)

print("Top 10 files with most clones:")
print(file_counts.head(10))
```

---

## トラブルシューティング

### 問題 1: 出力ファイルが空

**原因**:

- 検出されたクローンが検証閾値を超えなかった
- ソースディレクトリが空または対象ファイルがない

**確認方法**:

```bash
# clone_pairs ファイルを確認
cat clone_pairs

# 閾値を下げて再実行
java -jar NIL-all.jar -s /path/to/src -v 50 -f 5
```

### 問題 2: 類似度が予想より低い

**原因**:

- コメントや空白の違い
- 変数名の違い
- N-gram サイズが大きすぎる

**解決策**:

```bash
# N-gramサイズを小さくする
java -jar NIL-all.jar -s /path/to/src -n 3
```

### 問題 3: LCS 類似度が出力されない

**原因**:

- N-gram 類似度が検証閾値を超えていない

**確認方法**:

```bash
# N-gram類似度のみを確認
cut -d',' -f7 clone_pairs

# 検証閾値を下げる
java -jar NIL-all.jar -s /path/to/src -v 50
```

---

## まとめ

NIL の入出力は以下の特徴があります：

- **柔軟な入力**: 複数の言語と調整可能なパラメータ
- **明確な出力**: CSV 形式で解析しやすい
- **互換性**: BigCloneEval など既存ツールとの連携可能
- **追跡可能**: コミット情報による履歴管理

詳細な使用方法については、以下のドキュメントも参照してください：

- [使用ガイド](./NIL_USAGE_GUIDE.md)
- [Docker ガイド](./DOCKER_GUIDE.md)
- [アーキテクチャ](./ARCHITECTURE.md)
