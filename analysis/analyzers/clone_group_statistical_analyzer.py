#!/usr/bin/env python3
"""
クローングループ統計分析器（統合版）

削除されたグループとそうでないグループの比較分析を行う。
"""

from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
from config.settings import AnalysisConfig
from core.base_analyzer import BaseAnalyzer
from tqdm import tqdm


class CloneGroupStatisticalAnalyzer(BaseAnalyzer):
    """クローングループの統計分析器"""

    def __init__(self, config: AnalysisConfig):
        """
        初期化

        Args:
            config: 分析設定
        """
        super().__init__(config, "clone_group_statistical")

    def analyze_snapshot_with_tracing(
        self, snapshot_path: Path, tracing_path: Path
    ) -> Dict[str, pd.DataFrame]:
        """
        スナップショットをメソッド追跡データと組み合わせて分析

        Args:
            snapshot_path: スナップショットディレクトリのパス
            tracing_path: method_tracing.csvのパス

        Returns:
            分析結果の辞書
        """
        self.logger.info(f"スナップショット分析開始: {snapshot_path}")

        # データ読み込み
        data = self.load_snapshot_data(snapshot_path)
        tracing_df = self.data_loader.load_method_tracing(tracing_path)

        if "enhanced_code_blocks" not in data:
            self.logger.warning(f"必要なデータが見つかりません: {snapshot_path}")
            return {}

        enhanced_df = data["enhanced_code_blocks"]

        # 削除されたメソッドを特定
        deleted_methods = self.data_loader.identify_deleted_methods(tracing_df)

        # グループの削除状況を分析
        group_deletion_analysis = self._analyze_group_deletion_patterns(
            enhanced_df, deleted_methods
        )

        # 統計検定実行
        statistical_tests = self._perform_statistical_tests(
            enhanced_df, deleted_methods, group_deletion_analysis
        )

        # 結果をまとめる
        results = {
            "group_deletion_analysis": group_deletion_analysis,
            "statistical_tests": pd.DataFrame([statistical_tests]),
        }

        self.logger.info(f"スナップショット分析完了: {snapshot_path}")
        return results

    def analyze_all_snapshots_with_tracing(
        self, results_dir: Path, tracing_dir: Path
    ) -> Dict[str, pd.DataFrame]:
        """
        全スナップショットをメソッド追跡データと組み合わせて分析

        Args:
            results_dir: resultsディレクトリのパス
            tracing_dir: method_tracing.csvが格納されているディレクトリのパス

        Returns:
            全スナップショットの分析結果
        """
        self.logger.info(f"全スナップショット分析開始: {results_dir}")

        snapshot_dirs = [d for d in results_dir.iterdir() if d.is_dir()]
        snapshot_dirs.sort()

        all_results = {}
        summary_deletion_analysis = []

        for snapshot_dir in tqdm(snapshot_dirs, desc="スナップショット分析"):
            try:
                # 対応するmethod_tracing.csvを探す
                snapshot_name = snapshot_dir.name
                tracing_files = list(
                    tracing_dir.glob(f"{snapshot_name}_to_*/method_tracing.csv")
                )

                if tracing_files:
                    tracing_path = tracing_files[0]  # 最初のファイルを使用
                    snapshot_results = self.analyze_snapshot_with_tracing(
                        snapshot_dir, tracing_path
                    )

                    if snapshot_results:
                        # 個別結果を保存
                        all_results[snapshot_name] = snapshot_results

                        # 削除分析を収集
                        if "group_deletion_analysis" in snapshot_results:
                            deletion_df = snapshot_results[
                                "group_deletion_analysis"
                            ].copy()
                            deletion_df["snapshot"] = snapshot_name
                            summary_deletion_analysis.append(deletion_df)

            except Exception as e:
                self.logger.error(f"スナップショット分析エラー {snapshot_dir}: {e}")
                continue

        # 全スナップショットの削除分析をまとめる
        if summary_deletion_analysis:
            all_results["summary_deletion_analysis"] = pd.concat(
                summary_deletion_analysis, ignore_index=True
            )

        self.logger.info(
            f"全スナップショット分析完了: {len(all_results)}個のスナップショット"
        )
        return all_results

    def _analyze_group_deletion_patterns(
        self, enhanced_df: pd.DataFrame, deleted_methods: Set[str]
    ) -> pd.DataFrame:
        """
        グループの削除パターンを分析

        Args:
            enhanced_df: 拡張されたcode_blocks DataFrame
            deleted_methods: 削除されたメソッドのtoken_hashのセット

        Returns:
            グループ削除分析のDataFrame
        """
        self.logger.info("グループ削除パターン分析開始")

        # グループごとの分析
        group_analysis = []

        for group_id in enhanced_df["group_id"].unique():
            if group_id == -1:  # グループに属さないブロックはスキップ
                continue

            group_methods = enhanced_df[enhanced_df["group_id"] == group_id]
            group_size = len(group_methods)

            # 削除されたメソッド数をカウント
            deleted_count = sum(
                1
                for _, method in group_methods.iterrows()
                if method["token_hash"] in deleted_methods
            )

            # 削除割合を計算
            deletion_ratio = deleted_count / group_size if group_size > 0 else 0

            # グループの特徴量
            avg_similarity = (
                group_methods["avg_similarity"].iloc[0]
                if not group_methods.empty
                else 0
            )

            # 削除状態の分類
            if deletion_ratio == 0:
                deletion_status = "surviving"
            elif deletion_ratio == 1:
                deletion_status = "fully_deleted"
            else:
                deletion_status = "partially_deleted"

            group_analysis.append(
                {
                    "group_id": group_id,
                    "group_size": group_size,
                    "deleted_count": deleted_count,
                    "deletion_ratio": deletion_ratio,
                    "deletion_status": deletion_status,
                    "avg_similarity": avg_similarity,
                }
            )

        analysis_df = pd.DataFrame(group_analysis)

        # 削除状況の要約統計
        deletion_summary = (
            analysis_df.groupby("deletion_status")
            .agg(
                {
                    "group_id": "count",
                    "group_size": ["mean", "std", "min", "max"],
                    "avg_similarity": ["mean", "std", "min", "max"],
                    "deletion_ratio": ["mean", "std", "min", "max"],
                }
            )
            .round(3)
        )

        self.logger.info(
            f"グループ削除パターン分析完了: {len(analysis_df)}個のグループ"
        )
        return analysis_df

    def _perform_statistical_tests(
        self,
        enhanced_df: pd.DataFrame,
        deleted_methods: Set[str],
        group_deletion_analysis: pd.DataFrame,
    ) -> Dict:
        """
        統計検定を実行

        Args:
            enhanced_df: 拡張されたcode_blocks DataFrame
            deleted_methods: 削除されたメソッドのtoken_hashのセット
            group_deletion_analysis: グループ削除分析のDataFrame

        Returns:
            統計検定結果の辞書
        """
        self.logger.info("統計検定実行中...")

        # グループサイズの比較（完全削除 vs 生存）
        surviving_groups = group_deletion_analysis[
            group_deletion_analysis["deletion_status"] == "surviving"
        ]
        fully_deleted_groups = group_deletion_analysis[
            group_deletion_analysis["deletion_status"] == "fully_deleted"
        ]

        if len(surviving_groups) > 0 and len(fully_deleted_groups) > 0:
            # グループサイズの比較
            group_size_test = self.statistical_tester.mann_whitney_u_test(
                surviving_groups["group_size"],
                fully_deleted_groups["group_size"],
                "Group Size: Surviving vs Fully Deleted",
            )

            # 平均類似度の比較
            similarity_test = self.statistical_tester.mann_whitney_u_test(
                surviving_groups["avg_similarity"],
                fully_deleted_groups["avg_similarity"],
                "Average Similarity: Surviving vs Fully Deleted",
            )

            # 削除割合とグループサイズの相関
            correlation_test = self.statistical_tester.spearman_correlation_test(
                group_deletion_analysis["deletion_ratio"],
                group_deletion_analysis["group_size"],
                "Deletion Ratio vs Group Size",
            )

            statistical_tests = {
                "group_size_comparison": group_size_test,
                "similarity_comparison": similarity_test,
                "deletion_ratio_correlation": correlation_test,
            }
        else:
            self.logger.warning("統計検定に必要なデータが不足しています")
            statistical_tests = {}

        self.logger.info(f"統計検定完了: {len(statistical_tests)}個の検定")
        return statistical_tests

    def create_visualizations(
        self,
        enhanced_df: pd.DataFrame,
        deleted_methods: Set[str],
        group_deletion_analysis: pd.DataFrame,
    ) -> None:
        """
        可視化を作成

        Args:
            enhanced_df: 拡張されたcode_blocks DataFrame
            deleted_methods: 削除されたメソッドのtoken_hashのセット
            group_deletion_analysis: グループ削除分析のDataFrame
        """
        if not self.config.enable_visualization:
            return

        self.logger.info("可視化作成中...")

        # グループサイズの分布比較
        surviving_groups = group_deletion_analysis[
            group_deletion_analysis["deletion_status"] == "surviving"
        ]
        fully_deleted_groups = group_deletion_analysis[
            group_deletion_analysis["deletion_status"] == "fully_deleted"
        ]

        if len(surviving_groups) > 0 and len(fully_deleted_groups) > 0:
            # グループサイズの分布比較
            fig1 = self.visualizer.create_distribution_comparison(
                surviving_groups["group_size"],
                fully_deleted_groups["group_size"],
                ("Surviving Groups", "Fully Deleted Groups"),
                "Group Size Distribution Comparison",
                "Group Size",
            )
            self.save_visualization(fig1, "group_size_distribution_comparison.png")

            # 平均類似度の分布比較
            fig2 = self.visualizer.create_distribution_comparison(
                surviving_groups["avg_similarity"],
                fully_deleted_groups["avg_similarity"],
                ("Surviving Groups", "Fully Deleted Groups"),
                "Average Similarity Distribution Comparison",
                "Average Similarity",
            )
            self.save_visualization(fig2, "similarity_distribution_comparison.png")

            # 削除割合とグループサイズの散布図
            fig3 = self.visualizer.create_scatter_plot(
                group_deletion_analysis["group_size"],
                group_deletion_analysis["deletion_ratio"],
                "Deletion Ratio vs Group Size",
                "Group Size",
                "Deletion Ratio",
            )
            self.save_visualization(fig3, "deletion_ratio_vs_group_size.png")

        self.logger.info("可視化完了")

    def run_analysis(
        self,
        target_snapshots: Optional[List[str]] = None,
        tracing_dir: Optional[Path] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        分析を実行

        Args:
            target_snapshots: 対象スナップショットのリスト（Noneの場合は全スナップショット）
            tracing_dir: method_tracing.csvが格納されているディレクトリのパス

        Returns:
            分析結果の辞書
        """
        self.logger.info("クローングループ統計分析開始")

        if target_snapshots:
            # 指定されたスナップショットのみ分析
            results = {}
            for snapshot_name in target_snapshots:
                snapshot_path = self.config.results_dir / snapshot_name
                if snapshot_path.exists():
                    if tracing_dir:
                        # method_tracing.csvを探す
                        tracing_files = list(
                            tracing_dir.glob(f"{snapshot_name}_to_*/method_tracing.csv")
                        )
                        if tracing_files:
                            snapshot_results = self.analyze_snapshot_with_tracing(
                                snapshot_path, tracing_files[0]
                            )
                        else:
                            self.logger.warning(
                                f"method_tracing.csvが見つかりません: {snapshot_name}"
                            )
                            continue
                    else:
                        self.logger.warning(
                            "method_tracing.csvのディレクトリが指定されていません"
                        )
                        continue

                    if snapshot_results:
                        results[snapshot_name] = snapshot_results
                else:
                    self.logger.warning(
                        f"スナップショットが見つかりません: {snapshot_name}"
                    )
        else:
            # 全スナップショットを分析
            if tracing_dir:
                results = self.analyze_all_snapshots_with_tracing(
                    self.config.results_dir, tracing_dir
                )
            else:
                self.logger.warning(
                    "method_tracing.csvのディレクトリが指定されていません"
                )
                results = {}

        # 結果を保存
        self.save_results(results, "clone_group_statistical_")

        # 要約レポートを作成
        summary_report = self.create_summary_report(results)
        self.save_results(
            {"summary_report": summary_report}, "clone_group_statistical_"
        )

        # ログ出力
        self.log_analysis_summary(results)

        self.logger.info("クローングループ統計分析完了")
        return results
