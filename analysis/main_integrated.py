#!/usr/bin/env python3
"""
統合分析システムのメインエントリーポイント

新しいアーキテクチャに統合された分析器を使用して分析を実行する。
"""

import argparse
from pathlib import Path

from analyzers import (
    CloneGroupAnalyzer,
    CloneGroupStatisticalAnalyzer,
    MethodLevelFeatureAnalyzer,
)
from config.settings import AnalysisConfig


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="統合分析システム")
    parser.add_argument(
        "--analysis-type",
        choices=["clone_group", "method_level", "statistical", "all"],
        default="all",
        help="実行する分析のタイプ",
    )
    parser.add_argument(
        "--snapshots",
        nargs="*",
        help="分析対象のスナップショット名（指定しない場合は全スナップショット）",
    )
    parser.add_argument(
        "--tracing-dir",
        type=Path,
        help="method_tracing.csvが格納されているディレクトリのパス",
    )
    parser.add_argument(
        "--ngram-threshold", type=int, default=50, help="N-gram類似度の閾値"
    )
    parser.add_argument("--lcs-threshold", type=int, default=60, help="LCS類似度の閾値")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("../results"),
        help="resultsディレクトリのパス",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./output"),
        help="出力ディレクトリのパス",
    )
    parser.add_argument(
        "--disable-visualization", action="store_true", help="可視化を無効化"
    )
    parser.add_argument(
        "--disable-statistical-tests", action="store_true", help="統計検定を無効化"
    )

    args = parser.parse_args()

    # 設定を作成
    config = AnalysisConfig(
        ngram_threshold=args.ngram_threshold,
        lcs_threshold=args.lcs_threshold,
        results_dir=args.results_dir,
        output_dir=args.output_dir,
        enable_visualization=not args.disable_visualization,
        enable_statistical_tests=not args.disable_statistical_tests,
    )

    # 分析を実行
    if args.analysis_type in ["clone_group", "all"]:
        print("=== クローングループ分析実行 ===")
        clone_group_analyzer = CloneGroupAnalyzer(config)
        clone_group_results = clone_group_analyzer.run_analysis(args.snapshots)
        print(
            f"クローングループ分析完了: {len(clone_group_results)}個のスナップショット"
        )

    if args.analysis_type in ["method_level", "all"]:
        print("=== メソッドレベル特徴量分析実行 ===")
        method_level_analyzer = MethodLevelFeatureAnalyzer(config)
        method_level_results = method_level_analyzer.run_analysis(
            args.snapshots, args.tracing_dir
        )
        print(
            f"メソッドレベル特徴量分析完了: {len(method_level_results)}個のスナップショット"
        )

    if args.analysis_type in ["statistical", "all"]:
        print("=== クローングループ統計分析実行 ===")
        statistical_analyzer = CloneGroupStatisticalAnalyzer(config)
        statistical_results = statistical_analyzer.run_analysis(
            args.snapshots, args.tracing_dir
        )
        print(
            f"クローングループ統計分析完了: {len(statistical_results)}個のスナップショット"
        )

    print("=== 全分析完了 ===")


if __name__ == "__main__":
    main()
