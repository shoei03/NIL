# Method Evolution Tracking - Phase 1 & 2 Implementation

## 概要

メソッドの時系列追跡機能（Phase 1 & 2）が完了しました。この機能により、コードベースのスナップショット間でメソッドの進化を追跡できます。

### Phase 1: 完全一致ベースの追跡

- ファイルパス + メソッド名 + シグネチャによる exact matching
- TokenSequence ハッシュによる同一実装の検出

### Phase 2: 類似度ベースの追跡

- N-gram 類似度と LCS 類似度を使用した高度なマッチング
- リネーム、ファイル移動、シグネチャ変更、リファクタリングの検出
- NIL と同じアルゴリズム（N-gram 10%、LCS 70%）を使用

## 実装内容

### 1. code_blocks ファイルの拡張

#### 新しいフォーマット（Phase 2）

```
file,start,end,method,return_type,[params],commit_hash,token_hash,[token_sequence]
```

**例:**

```
/app/Repos/pandas/pandas/core/index.py,30,40,__new__,None,[cls:Any;data:Any;dtype:Any;copy:Any],test_token,0c362c81595e07713cf135cb0aaa4389,[99333;1237986720;98602;3076010;...]
```

#### 追加された情報

- **commit_hash**: Git コミットハッシュ（8 桁）
- **token_hash**: トークン列の MD5 ハッシュ（メソッド実装の一意識別子）
- **token_sequence**: トークン列（整数のリスト、セミコロン区切り） ← **Phase 2 で追加**

**ファイルサイズ**: TokenSequence 追加により約 6-7 倍に増加（46KB → 295KB）

### 2. スナップショット別保存

`-ch, --commit-hash`と`-ct, --commit-timestamp`オプションを使用すると、code_blocks ファイルがスナップショット別に`code_blocks/`ディレクトリに保存されます：

```bash
code_blocks/
  ├── code_blocks_20111010_015605_87a3370b
  ├── code_blocks_20120209_113131_71b65ab6
  ├── code_blocks_20130212_043101_13c5d72a
  └── ...
```

**ファイル名形式**: `code_blocks_<YYYYMMDD_HHMMSS>_<commit_hash>`

- タイムスタンプ: コミット日時（`YYYYMMDD_HHMMSS`形式）
- コミットハッシュ: 最初の 8 文字

このディレクトリ構造により、ルートディレクトリが散らからず、スナップショットファイルを整理された状態で管理できます。また、ファイル名にタイムスタンプが含まれることで、時系列順のソートが容易になります。

### 3. Method Tracker（メソッド追跡スクリプト）

#### Phase 1 の機能

- **完全一致検出** (`exact`): ファイルパス + メソッド名 + シグネチャによる追跡
- **TokenHash マッチング** (`token_hash`): 同一実装（異なる名前・場所）の検出
- **変更検出**: 追加 (added)、削除 (deleted)

#### Phase 2 の機能（`--use-similarity`で有効化）

- **リネーム検出** (`renamed`): 同ファイル内、高類似度（LCS ≥ 90%）
- **ファイル移動検出** (`moved`): 異なるファイル、高類似度（LCS ≥ 90%）
- **シグネチャ変更** (`signature_changed`): 同ファイル、同メソッド名、異なる引数
- **リファクタリング** (`refactored`): 中程度の類似度（LCS ≥ 70%）

#### 類似度計算アルゴリズム

- **N-gram 類似度**: フィルタリング閾値 10%（NIL と同じ）
- **LCS 類似度**: 検証閾値 70%（NIL と同じ）
- **Hunt-Szymanski LCS**: O(N log N)の高速アルゴリズム

#### 使用方法

```bash
# NILでスナップショットを生成
./scripts/nil.sh /app/Repos/pandas -c <commit_hash>

# または、バッチモードで複数のスナップショットを生成
# （タイムスタンプとコミットハッシュが自動的に付与されます）
./scripts/nil.sh /app/Repos/pandas --batch --skip 1000
```

### method_tracker.py

`code_blocks/`ディレクトリ内の複数の code_blocks ファイルを使用してメソッド追跡を行います：

```bash
python analysis/method_tracker.py \
  -i code_blocks \
  -o analysis/output/tracking_results \
  --log analysis/logs/tracking.log
```

**注意**: `method_tracker.py`は新しいファイル名形式（`code_blocks_<timestamp>_<hash>`）と古い形式（`code_blocks_<hash>`）の両方に対応しています。

#### オプション

- `-i, --input`: code_blocks ファイルまたはそれらを含むディレクトリのパス（必須）
  - ディレクトリを指定すると、その中の全ての code_blocks ファイルを自動検出して処理
- `-o, --output`: 出力ディレクトリ（必須）
- `--log`: ログファイルパス（オプション）
- `--use-similarity`: Phase 2 の類似度ベースマッチングを有効化
- `--ngram-threshold`: N-gram 類似度閾値（デフォルト: 10%、NIL と同じ）
- `--lcs-threshold`: LCS 類似度閾値（デフォルト: 70%、NIL と同じ）

#### Phase 1 の実行例（基本）

```bash
python analysis/method_tracker.py \
  -i code_blocks \
  -o analysis/output/tracking_results \
  --log analysis/logs/tracking.log
```

#### Phase 2 の実行例（類似度マッチング有効）

```bash
python analysis/method_tracker.py \
  -i code_blocks \
  -o analysis/output/tracking_results \
  --log analysis/logs/tracking.log \
  --use-similarity
```

````

#### 出力ファイル

##### 1. `method_tracking_summary.csv`
スナップショット間の変更サマリー

```csv
snapshot_t,snapshot_t1,exact_matches,added_methods,deleted_methods,total_t,total_t1
219809a5,4e375e8e,322,1,0,322,323
a56b0056,bad5cdc6,192,130,73,265,322
````

##### 2. `method_tracking_details.csv`

詳細な変更情報

```csv
snapshot_t,snapshot_t1,change_type,file_path,method_name,signature,line_range_t,line_range_t1,commit_t,commit_t1
219809a5,4e375e8e,added,/app/Repos/pandas/pandas/core/frame.py,asfreq,asfreq:self:Any;freq:Any;fillMethod:Any:None,,670-694,,4e375e8e
219809a5,4e375e8e,exact_match,/app/Repos/pandas/doc/sphinxext/compiler_unparse.py,_Function,_Function:self:Any;t:Any:None,253-276,253-276,219809a5,4e375e8e
```

## 実装の詳細

### Kotlin の変更

#### 1. CodeBlock.kt

```kotlin
data class CodeBlock(
    // ... existing fields ...
    val commitHash: String? = null,
) {
    fun getTokenSequenceHash(): String {
        // TokenSequenceのMD5ハッシュを計算
    }
}
```

#### 2. NILConfig.kt

新しいオプション `-ch, --commit-hash` を追加

#### 3. Preprocess.kt

```kotlin
abstract class Preprocess(
    private val threads: Int,
    private val commitHash: String? = null
) {
    fun collectTokenSequences(src: File): List<TokenSequence> {
        val codeBlockFileName = if (commitHash != null) {
            "${CODE_BLOCK_FILE_NAME}_${commitHash.take(8)}"
        } else {
            CODE_BLOCK_FILE_NAME
        }
        // ...
    }
}
```

### Python スクリプト

#### method_tracker.py

```python
class MethodTracker:
    def parse_code_blocks(self, file_path: Path) -> Dict[str, MethodInfo]
    def find_exact_matches(...) -> List[MethodMatch]
    def analyze_changes(...) -> Tuple[List[MethodMatch], Set[str], Set[str]]
    def track_methods(self, code_blocks_dir: Path, output_dir: Path)
```

## テスト結果

### テストケース 1: 連続したコミット

- **219809a5 → 4e375e8e**
  - exact_matches: 322
  - added: 1 (`asfreq`メソッド)
  - deleted: 0

### テストケース 2: 離れたコミット

- **a56b0056 → bad5cdc6**
  - exact_matches: 192
  - added: 130
  - deleted: 73

## Phase 2 の実装状況

### ✅ 実装完了した機能

1. **TokenSequence 保存**: code_blocks ファイルにトークン列を保存
2. **類似度計算**: N-gram 類似度と LCS 類似度（NIL と同じアルゴリズム）
3. **マッチング戦略**:
   - TokenHash マッチング: 同一実装の検出
   - リネーム検出: 同ファイル内、高類似度（LCS ≥ 90%）
   - ファイル移動検出: 異なるファイル、高類似度（LCS ≥ 90%）
   - シグネチャ変更: 同ファイル、同メソッド名、異なる引数
   - リファクタリング: 中程度の類似度（LCS ≥ 70%）

### 使用方法

```bash
# Phase 2を有効にしてメソッド追跡
cd analysis
docker compose run --rm analysis python method_tracker.py \
  -i /workspace \
  -o /app/output/phase2_tracking \
  --use-similarity \
  --ngram-threshold 10 \
  --lcs-threshold 70
```

### パフォーマンス

- N-gram 類似度: O(N) - 高速フィルタリング
- LCS 類似度: O(N log N) - Hunt-Szymanski アルゴリズム
- ファイルサイズ: 約 6-7 倍増加（TokenSequence 保存のため）

## 将来の拡張（Phase 3）

- メソッド分割/統合の検出
- より複雑なリファクタリングパターンの識別
- 変更理由の自動推論

## 関連ファイル

### Kotlin

- `src/main/kotlin/jp/ac/osaka_u/sdl/nil/entity/CodeBlock.kt`
- `src/main/kotlin/jp/ac/osaka_u/sdl/nil/NILConfig.kt`
- `src/main/kotlin/jp/ac/osaka_u/sdl/nil/usecase/preprocess/Preprocess.kt`
- `src/main/kotlin/jp/ac/osaka_u/sdl/nil/usecase/preprocess/*/`

### Python

- `analysis/method_tracker.py` - メソッド追跡スクリプト（Phase 1 & 2）
- `analysis/similarity_calculator.py` - N-gram/LCS 類似度計算（Phase 2）

### Shell

- `scripts/nil.sh`

### ドキュメント

- `analysis/README.md`

## 使用例

### シンプルな使用例

```bash
# 1. 特定のコミットでNILを実行
./scripts/nil.sh /app/Repos/pandas -c abc123def

# 2. 別のコミットでNILを実行
./scripts/nil.sh /app/Repos/pandas -c def456ghi

# 3. メソッド追跡を実行
cd analysis
docker compose run --rm analysis python method_tracker.py \
  -i /workspace \
  -o /app/output/tracking
```

### バッチ処理の例

```bash
# 1000コミット間隔で複数スナップショット生成
./scripts/nil.sh /app/Repos/pandas --batch --skip 1000

# メソッド追跡を実行
cd analysis
docker compose run --rm analysis python method_tracker.py \
  -i /workspace \
  -o /app/output/batch_tracking \
  --log /app/logs/batch_tracking.log
```

## 参考資料

- [AGENTS.md](./AGENTS.md) - 実装における注意点
- [analysis/README.md](./analysis/README.md) - 分析スクリプトの詳細
- [EXPERIMENT.md](./EXPERIMENT.md) - 実験手順
