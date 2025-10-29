#!/usr/bin/env python3
"""
統合分析システムの README

新しいアーキテクチャに統合された分析システムの使用方法を説明する。
"""

# 統合分析システム

このディレクトリには、リファクタリングされた統合分析システムが含まれています。

## ディレクトリ構造

```
analysis/
├── core/                           # コア機能
│   ├── base_analyzer.py           # 基底分析クラス
│   ├── data_loader.py             # データ読み込み統一
│   ├── graph_utils.py             # グラフ操作ユーティリティ
│   ├── statistical_tester.py      # 統計検定統一
│   └── visualizer.py              # 可視化統一
├── config/                         # 設定管理
│   └── settings.py                # 設定クラス
├── analyzers/                      # 分析器
│   ├── clone_group_analyzer.py    # クローングループ分析器
│   ├── method_level_feature_analyzer.py  # メソッドレベル特徴量分析器
│   └── clone_group_statistical_analyzer.py  # クローングループ統計分析器
├── main_integrated.py              # 統合メインスクリプト
└── *.py.old                       # 古いファイル（バックアップ）
```

## 使用方法

### 基本的な使用方法

```bash
# 全分析を実行
uv run python main_integrated.py --analysis-type all

# 特定の分析のみ実行
uv run python main_integrated.py --analysis-type clone_group

# 特定のスナップショットのみ分析
uv run python main_integrated.py --analysis-type all --snapshots 20171124_011347_b45325e2

# メソッド追跡データと組み合わせた分析
uv run python main_integrated.py --analysis-type method_level --tracing-dir output/pair_diff_with_lists
```

### オプション

- `--analysis-type`: 実行する分析のタイプ（clone_group, method_level, statistical, all）
- `--snapshots`: 分析対象のスナップショット名（指定しない場合は全スナップショット）
- `--tracing-dir`: method_tracing.csv が格納されているディレクトリのパス
- `--ngram-threshold`: N-gram 類似度の閾値（デフォルト: 50）
- `--lcs-threshold`: LCS 類似度の閾値（デフォルト: 60）
- `--results-dir`: results ディレクトリのパス（デフォルト: ../results）
- `--output-dir`: 出力ディレクトリのパス（デフォルト: ./output）
- `--disable-visualization`: 可視化を無効化
- `--disable-statistical-tests`: 統計検定を無効化

## 分析器の詳細

### 1. CloneGroupAnalyzer

- クローンペアからグラフ理論の連結成分を用いてクローンのグループを作成
- code_blocks.csv にグループ情報を追加

### 2. MethodLevelFeatureAnalyzer

- 各メソッドに対して詳細な特徴量を計算
- 高類似度メソッド数、中類似度メソッド数など
- 削除されたメソッドと残存メソッドの比較

### 3. CloneGroupStatisticalAnalyzer

- 削除されたグループとそうでないグループの比較分析
- 統計検定と可視化

## 設定

設定は`config/settings.py`の`AnalysisConfig`クラスで管理されています。

## 出力

各分析器は`output/`ディレクトリ以下に結果を保存します：

- `output/clone_group/`: クローングループ分析の結果
- `output/method_level_feature/`: メソッドレベル特徴量分析の結果
- `output/clone_group_statistical/`: クローングループ統計分析の結果

## リファクタリングの利点

1. **コードの重複削除**: 共通機能を基底クラスに集約
2. **責任の明確化**: 各クラスが単一の責任を持つ
3. **設定の統一**: 全分析器で同じ設定を使用
4. **拡張性の向上**: 新しい分析器を簡単に追加可能
5. **保守性の向上**: 統一されたインターフェースとログ管理
