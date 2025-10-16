# NIL 使用ガイド

このドキュメントでは、NIL（N-gram, Inverted index, LCS）クローン検出ツールの動作原理、Docker 実行方法、入出力形式について説明します。

## 目次

1. [NIL の動作原理](#nilの動作原理)
2. [Docker 実行方法](#docker実行方法)
3. [入出力形式](#入出力形式)
4. [実行例](#実行例)

---

## NIL の動作原理

NIL は、大規模コードベースに対してスケーラブルなクローン検出を実現するツールです。以下の 3 つのフェーズで動作します。

### 1. 前処理フェーズ (Preprocess Phase)

ソースコードをトークン列に変換します。

- **入力**: ソースコードファイル（Java, C, C++, C#, Python, Kotlin）
- **処理**:
  - ANTLR を使用した字句解析
  - トークン正規化（記号分離、識別子の抽象化）
  - 最小行数・最小トークン数によるフィルタリング
- **出力**: トークン列のリスト（TokenSequence）

### 2. クローン検出フェーズ (Clone Detection Phase)

N-gram ベースの転置インデックスを用いた効率的なクローン検出を行います。

#### 2.1 位置特定 (Location)

- N-gram を用いた転置インデックスにより、類似コード片の候補を高速に特定
- パーティション分割により大規模コードベースに対応

#### 2.2 フィルタリング (Filtration)

- N-gram 類似度を計算
- フィルタリング閾値（デフォルト: 10%）以下のペアを除外

#### 2.3 検証 (Verification)

- **N-gram ベース検証**: 検証閾値（デフォルト: 70%）による絞り込み
- **LCS ベース検証**: Hunt-Szymanski アルゴリズムによる厳密な類似度計算

### 3. 出力フェーズ (Output Phase)

検出されたクローンペアを指定された形式で出力します。

---

## Docker 実行方法

### 前提条件

- Docker がインストールされていること
- Docker Compose がインストールされていること（オプション）

### 方法 1: Docker Compose を使用

1. **NIL リポジトリをクローン**

```bash
git clone https://github.com/kusumotolab/NIL
cd NIL
```

2. **Docker コンテナをビルドして起動**

```bash
docker-compose up -d
```

3. **コンテナに入る**

```bash
docker-compose exec nil bash
```

4. **NIL をビルド**

```bash
./gradlew shadowJar
```

5. **NIL を実行**

```bash
java -jar ./build/libs/NIL-all.jar -s /path/to/source -o /app/results/output.csv
```

6. **結果を確認**

結果ファイルは `/app` ディレクトリ配下（ホストマシンの `NIL` ディレクトリと同期）に出力されます。

7. **コンテナから退出**

```bash
exit
```

8. **コンテナを停止**

```bash
docker-compose down
```

### 方法 2: Docker を直接使用

1. **イメージをビルド**

```bash
docker build -t nil .
```

2. **コンテナを起動してマウント**

```bash
docker run -it -v $(pwd):/app nil
```

3. **以降は方法 1 の手順 4-7 と同様**

### Docker での実行時の注意点

- ソースコードディレクトリは `/app` にマウントされたディレクトリ配下を指定してください
- 出力ファイルも `/app` 配下に指定することで、ホストマシンからアクセス可能になります
- パフォーマンスを最適化するには `-t` オプションでスレッド数を調整してください

---

## 入出力形式

### 入力

#### コマンドライン引数

| オプション                             | 必須 | 説明                                  | デフォルト値             |
| -------------------------------------- | ---- | ------------------------------------- | ------------------------ |
| `-s`, `--src`                          | ✓    | 解析対象のソースディレクトリ          | なし                     |
| `-mil`, `--min-line`                   |      | クローンとみなす最小行数              | 6                        |
| `-mit`, `--min-token`                  |      | クローンとみなす最小トークン数        | 50                       |
| `-n`, `--n-gram`                       |      | N-gram の N 値                        | 5                        |
| `-p`, `--partition-number`             |      | パーティション数                      | 10                       |
| `-f`, `--filtration-threshold`         |      | フィルタリング閾値（%）               | 10                       |
| `-v`, `--verification-threshold`       |      | 検証閾値（%）                         | 70                       |
| `-o`, `--output`                       |      | 出力ファイルパス                      | `result_{n}_{f}_{v}.csv` |
| `-t`, `--threads`                      |      | 並列実行スレッド数                    | 全スレッド               |
| `-l`, `--language`                     |      | 対象言語（java/c/cpp/cs/py/kt）       | java                     |
| `-bce`, `--bigcloneeval`               |      | BigCloneEval 互換形式で出力           | false                    |
| `-mif`, `--mutationinjectionframework` |      | MutationInjectionFramework 互換モード | false                    |
| `-ch`, `--commit-hash`                 |      | コミットハッシュ（追跡用）            | なし                     |
| `-ct`, `--commit-timestamp`            |      | コミットタイムスタンプ（追跡用）      | なし                     |

#### 対応言語

| 言語   | オプション値   | 拡張子         |
| ------ | -------------- | -------------- |
| Java   | `java`         | `.java`        |
| C      | `c`            | `.c`, `.h`     |
| C++    | `cpp`          | `.cpp`, `.hpp` |
| C#     | `cs`, `csharp` | `.cs`          |
| Python | `py`, `python` | `.py`          |
| Kotlin | `kt`, `kotlin` | `.kt`          |

### 出力

#### 標準出力形式（デフォルト）

CSV 形式で以下のフィールドを出力します：

```csv
/path/to/file_A,start_line_A,end_line_A,/path/to/file_B,start_line_B,end_line_B,ngram_similarity,lcs_similarity
```

**フィールド説明:**

- `file_A`: クローンペアの 1 つ目のファイルパス
- `start_line_A`: 1 つ目のクローンの開始行
- `end_line_A`: 1 つ目のクローンの終了行
- `file_B`: クローンペアの 2 つ目のファイルパス
- `start_line_B`: 2 つ目のクローンの開始行
- `end_line_B`: 2 つ目のクローンの終了行
- `ngram_similarity`: N-gram ベース類似度（%）
- `lcs_similarity`: LCS ベース類似度（%）（LCS 検証が実行された場合のみ）

**例:**

```csv
/project/src/Main.java,10,25,/project/src/Helper.java,50,65,85.5,78.2
/project/src/Utils.java,100,120,/project/src/Common.java,30,50,92.3,88.7
```

#### BigCloneEval 互換形式（`-bce`オプション使用時）

```csv
dir_A,file_A,start_line_A,end_line_A,dir_B,file_B,start_line_B,end_line_B,ngram_similarity,lcs_similarity
```

**フィールド説明:**

- `dir_A`: 1 つ目のクローンのディレクトリパス
- `file_A`: 1 つ目のクローンのファイル名
- `start_line_A`: 1 つ目のクローンの開始行
- `end_line_A`: 1 つ目のクローンの終了行
- `dir_B`: 2 つ目のクローンのディレクトリパス
- `file_B`: 2 つ目のクローンのファイル名
- `start_line_B`: 2 つ目のクローンの開始行
- `end_line_B`: 2 つ目のクローンの終了行
- `ngram_similarity`: N-gram ベース類似度（%）
- `lcs_similarity`: LCS ベース類似度（%）

### 中間ファイル

実行中に以下の中間ファイルが生成されます：

- `clone_pairs`: クローンペアの ID と類似度情報（内部形式）
- `code_blocks/code_blocks_<timestamp>_<hash>`: トークン化されたコードブロック情報

---

## 実行例

### 基本的な実行

```bash
java -jar NIL-all.jar -s /path/to/source
```

結果は `result_5_10_70.csv` に出力されます。

### カスタムパラメータでの実行

```bash
java -jar NIL-all.jar \
  -s /path/to/source \
  -mil 10 \
  -mit 100 \
  -n 7 \
  -f 15 \
  -v 80 \
  -o /path/to/output/clones.csv \
  -t 8 \
  -l java
```

### Python プロジェクトの解析

```bash
java -jar NIL-all.jar -s /path/to/python/project -l py -o python_clones.csv
```

### BigCloneEval 形式での出力

```bash
java -jar NIL-all.jar -s /path/to/source -bce -o bce_result.csv
```

### Docker での実行例

```bash
docker-compose up -d
docker-compose exec nil bash
./gradlew shadowJar
java -jar ./build/libs/NIL-all.jar -s ./Repos/pandas -l py -o ./results/pandas_clones.csv
exit
docker-compose down
```

### 大規模コードベース（250-MLOC）の解析

大規模なコードベースに対しては、パーティション数を増やすことを推奨します：

```bash
java -jar NIL-all.jar -s /path/to/large/codebase -p 135 -t 16
```

---

## パフォーマンスチューニング

### パーティション数（`-p`）

- **小規模プロジェクト**（< 10,000 ファイル）: デフォルト（10）
- **中規模プロジェクト**（10,000 - 100,000 ファイル）: 30-50
- **大規模プロジェクト**（> 100,000 ファイル）: 100-135

### スレッド数（`-t`）

- CPU コア数に応じて設定
- 推奨: 物理コア数 × 1.5 - 2

### 閾値設定

- **フィルタリング閾値**（`-f`）: 低いほど多くの候補を検証（処理時間増加）
- **検証閾値**（`-v`）: 高いほど厳格なクローン検出（検出数減少）

---

## トラブルシューティング

### メモリ不足エラー

Java ヒープサイズを増やして実行：

```bash
java -Xmx8g -jar NIL-all.jar -s /path/to/source
```

### 処理が遅い

- パーティション数を増やす（`-p`）
- スレッド数を最適化（`-t`）
- フィルタリング閾値を上げる（`-f`）

### サポートされていない言語

現在サポートされている言語は Java, C, C++, C#, Python, Kotlin のみです。他の言語については将来のバージョンで対応予定です。

---

## 参考文献

詳細なアルゴリズムと評価については、以下の論文を参照してください：

- FSE '21 paper: [camera-ready.pdf](../camera-ready.pdf)
- DOI: 10.5281/zenodo.4492665
