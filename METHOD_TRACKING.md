# Method Evolution Tracking - Phase 1 Implementation

## 概要

メソッドの時系列追跡機能の基礎実装（Phase 1）が完了しました。この機能により、コードベースのスナップショット間でメソッドの進化を追跡できます。

## 実装内容

### 1. code_blocks ファイルの拡張

#### 新しいフォーマット

```
file,start,end,method,return_type,[params],commit_hash,token_hash
```

**例:**

```
/app/Repos/pandas/asv_bench/benchmarks/gil.py,39,87,run_parallel,None,[num_threads:Any;kwargs_list:Any],db31f6a3,1f2ab0673e47c4ad2b3cbf17a3d0e44a
```

#### 追加された情報

- **commit_hash**: Git コミットハッシュ（8 桁）
- **token_hash**: トークン列の MD5 ハッシュ（メソッド実装の一意識別子）

### 2. スナップショット別保存

`-ch, --commit-hash`オプションを使用すると、code_blocks ファイルがスナップショット別に`code_blocks/`ディレクトリに保存されます：

```bash
code_blocks/
  ├── code_blocks_9d008057
  ├── code_blocks_a56b0056
  ├── code_blocks_4e375e8e
  └── ...
```

このディレクトリ構造により、ルートディレクトリが散らからず、スナップショットファイルを整理された状態で管理できます。

### 3. Method Tracker（メソッド追跡スクリプト）

#### 機能

- **完全一致検出**: ファイルパス + メソッド名 + シグネチャによる追跡
- **変更検出**:
  - 追加されたメソッド (added)
  - 削除されたメソッド (deleted)
  - 維持されたメソッド (exact match)

#### 使用方法

````bash
# NILでスナップショットを生成
./scripts/nil.sh /app/Repos/pandas -c <commit_hash>

# または、バッチモードで複数のスナップショットを生成
./scripts/nil.sh /app/Repos/pandas --batch --skip 1000

### method_tracker.py

`code_blocks/`ディレクトリ内の複数のcode_blocksファイルを使用してメソッド追跡を行います：

```bash
python analysis/method_tracker.py \
  -i code_blocks \
  -o analysis/output/tracking_results \
  --log analysis/logs/tracking.log
````

#### オプション

- `-i, --input`: code_blocks ファイルまたはそれらを含むディレクトリのパス（デフォルト: `code_blocks`）
  - ディレクトリを指定すると、その中の全ての code_blocks ファイルを自動検出して処理
- `-o, --output`: 出力ディレクトリ（デフォルト: `analysis/output`）
- `--log`: ログファイルパス（デフォルト: `analysis/logs/method_tracker.log`）

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

## 制限事項（Phase 1）

現在の実装では以下の制限があります：

1. **完全一致のみ**: メソッド名とシグネチャの完全一致のみを検出
2. **リネーム未対応**: メソッド名が変更された場合は追跡できない
3. **シグネチャ変更未対応**: 引数が変更された場合は追跡できない
4. **ファイル移動未対応**: ファイルが移動された場合は追跡できない

これらは、Phase 2（類似度ベースのマッチング）で対応予定です。

## 次のステップ（Phase 2）

### 類似度ベースのマッチング

1. **TokenSequence ハッシュ比較**: 完全一致の高速検出
2. **N-gram 類似度**: 部分的な変更に対応
3. **LCS 類似度**: より精密な比較

### 検出可能な変更タイプ

- リネーム (同ファイル内、高類似度)
- シグネチャ変更 (引数追加/削除)
- ファイル移動 (異なるファイル、高類似度)
- リファクタリング (メソッド分割/統合)

## 関連ファイル

### Kotlin

- `src/main/kotlin/jp/ac/osaka_u/sdl/nil/entity/CodeBlock.kt`
- `src/main/kotlin/jp/ac/osaka_u/sdl/nil/NILConfig.kt`
- `src/main/kotlin/jp/ac/osaka_u/sdl/nil/usecase/preprocess/Preprocess.kt`
- `src/main/kotlin/jp/ac/osaka_u/sdl/nil/usecase/preprocess/*/`

### Python

- `analysis/method_tracker.py`

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
