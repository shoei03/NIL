#!/usr/bin/env python3
"""
メソッドレベルの特徴量分析器（統合版）

各メソッドに対して、高類似度メソッド数、中類似度メソッド数などの詳細な特徴量を計算する。
"""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from config.settings import AnalysisConfig, SimilarityThresholds
from core.base_analyzer import BaseAnalyzer
from tqdm import tqdm


class MethodLevelFeatureAnalyzer(BaseAnalyzer):
    """メソッドレベルの特徴量分析器"""

    def __init__(self, config: AnalysisConfig):
        """
        初期化

        Args:
            config: 分析設定
        """
        super().__init__(config, "method_level_feature")

        # 類似度閾値の設定
        self.thresholds = SimilarityThresholds()

    def analyze_snapshot(self, snapshot_path: Path) -> Dict[str, pd.DataFrame]:
        """
        スナップショットを分析

        Args:
            snapshot_path: スナップショットディレクトリのパス

        Returns:
            分析結果の辞書
        """
        self.logger.info(f"スナップショット分析開始: {snapshot_path}")

        # データ読み込み
        data = self.load_snapshot_data(snapshot_path)

        if "enhanced_code_blocks" not in data or "clone_pairs" not in data:
            self.logger.warning(f"必要なデータが見つかりません: {snapshot_path}")
            return {}

        enhanced_df = data["enhanced_code_blocks"]
        pairs_df = data["clone_pairs"]

        # メソッドレベルの特徴量を計算
        method_features = self._calculate_method_features(enhanced_df, pairs_df)

        # 結果をまとめる
        results = {"method_features": method_features}

        self.logger.info(f"スナップショット分析完了: {snapshot_path}")
        return results

    def analyze_with_tracing(
        self, snapshot_path: Path, tracing_path: Path
    ) -> Dict[str, pd.DataFrame]:
        """
        メソッド追跡データと組み合わせて分析

        Args:
            snapshot_path: スナップショットディレクトリのパス
            tracing_path: method_tracing.csvのパス

        Returns:
            分析結果の辞書
        """
        self.logger.info(f"メソッド追跡データと組み合わせた分析開始: {snapshot_path}")

        # データ読み込み
        data = self.load_snapshot_data(snapshot_path)
        tracing_df = self.data_loader.load_method_tracing(tracing_path)

        if "enhanced_code_blocks" not in data or "clone_pairs" not in data:
            self.logger.warning(f"必要なデータが見つかりません: {snapshot_path}")
            return {}

        enhanced_df = data["enhanced_code_blocks"]
        pairs_df = data["clone_pairs"]

        # 削除されたメソッドを特定
        deleted_methods = self.data_loader.identify_deleted_methods(tracing_df)

        # メソッドレベルの特徴量を計算
        method_features = self._calculate_method_features(enhanced_df, pairs_df)

        # 削除状態を追加
        method_features["is_deleted"] = method_features["token_hash"].isin(
            deleted_methods
        )

        # 統計検定実行
        statistical_tests = self._perform_method_level_tests(method_features)

        # 結果をまとめる
        results = {
            "method_features": method_features,
            "statistical_tests": pd.DataFrame([statistical_tests]),
        }

        self.logger.info(f"メソッド追跡データと組み合わせた分析完了: {snapshot_path}")
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
        summary_features = []

        for snapshot_dir in tqdm(snapshot_dirs, desc="スナップショット分析"):
            try:
                # 対応するmethod_tracing.csvを探す
                snapshot_name = snapshot_dir.name
                tracing_path = tracing_dir / f"{snapshot_name}_to_*/method_tracing.csv"
                tracing_files = list(
                    tracing_dir.glob(f"{snapshot_name}_to_*/method_tracing.csv")
                )

                if tracing_files:
                    tracing_path = tracing_files[0]  # 最初のファイルを使用
                    snapshot_results = self.analyze_with_tracing(
                        snapshot_dir, tracing_path
                    )
                else:
                    # method_tracing.csvがない場合は通常の分析
                    snapshot_results = self.analyze_snapshot(snapshot_dir)

                if snapshot_results:
                    # 個別結果を保存
                    all_results[snapshot_name] = snapshot_results

                    # 特徴量を収集
                    if "method_features" in snapshot_results:
                        features_df = snapshot_results["method_features"].copy()
                        features_df["snapshot"] = snapshot_name
                        summary_features.append(features_df)

            except Exception as e:
                self.logger.error(f"スナップショット分析エラー {snapshot_dir}: {e}")
                continue

        # 全スナップショットの特徴量をまとめる
        if summary_features:
            all_results["summary_features"] = pd.concat(
                summary_features, ignore_index=True
            )

        self.logger.info(
            f"全スナップショット分析完了: {len(all_results)}個のスナップショット"
        )
        return all_results

    def _calculate_method_features(
        self, enhanced_df: pd.DataFrame, pairs_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        メソッドレベルの特徴量を計算

        Args:
            enhanced_df: 拡張されたcode_blocks DataFrame
            pairs_df: clone_pairs DataFrame

        Returns:
            特徴量が追加されたDataFrame
        """
        self.logger.info("メソッドレベル特徴量計算開始")

        features_df = enhanced_df.copy()

        # 各メソッドの特徴量を計算
        method_features = []

        for _, method_row in tqdm(
            features_df.iterrows(), total=len(features_df), desc="特徴量計算"
        ):
            method_hash = method_row["token_hash"]
            features = self._calculate_single_method_features(method_hash, pairs_df)
            method_features.append(features)

        # 特徴量をDataFrameに追加
        features_df = pd.concat([features_df, pd.DataFrame(method_features)], axis=1)

        self.logger.info(
            f"メソッドレベル特徴量計算完了: {len(features_df)}個のメソッド"
        )
        return features_df

    def _calculate_single_method_features(
        self, method_hash: str, pairs_df: pd.DataFrame
    ) -> Dict:
        """
        単一メソッドの特徴量を計算

        Args:
            method_hash: メソッドのtoken_hash
            pairs_df: clone_pairs DataFrame

        Returns:
            特徴量の辞書
        """
        # このメソッドを含むペアを取得
        method_pairs = pairs_df[
            (pairs_df["block_id1"] == method_hash)
            | (pairs_df["block_id2"] == method_hash)
        ]

        if method_pairs.empty:
            return self._get_empty_features()

        # 類似度を計算
        similarities = []
        for _, pair in method_pairs.iterrows():
            similarity = self.data_loader.get_effective_similarity(
                pair["ngram_similarity"], pair["lcs_similarity"]
            )
            similarities.append(similarity)

        # 特徴量を計算
        features = {
            "high_similarity_count": sum(
                1 for s in similarities if s >= self.thresholds.HIGH
            ),
            "medium_similarity_count": sum(
                1
                for s in similarities
                if self.thresholds.MEDIUM <= s < self.thresholds.HIGH
            ),
            "low_similarity_count": sum(
                1
                for s in similarities
                if self.thresholds.LOW <= s < self.thresholds.MEDIUM
            ),
            "very_low_similarity_count": sum(
                1 for s in similarities if s < self.thresholds.LOW
            ),
            "max_similarity": max(similarities) if similarities else 0,
            "min_similarity": min(similarities) if similarities else 0,
            "avg_similarity": sum(similarities) / len(similarities)
            if similarities
            else 0,
            "std_similarity": pd.Series(similarities).std() if similarities else 0,
            "median_similarity": pd.Series(similarities).median()
            if similarities
            else 0,
            "similarity_range": max(similarities) - min(similarities)
            if similarities
            else 0,
            "high_similarity_ratio": sum(
                1 for s in similarities if s >= self.thresholds.HIGH
            )
            / len(similarities)
            if similarities
            else 0,
            "connectivity_score": len(similarities),
        }

        return features

    def _get_empty_features(self) -> Dict:
        """空の特徴量辞書を返す"""
        return {
            "high_similarity_count": 0,
            "medium_similarity_count": 0,
            "low_similarity_count": 0,
            "very_low_similarity_count": 0,
            "max_similarity": 0,
            "min_similarity": 0,
            "avg_similarity": 0,
            "std_similarity": 0,
            "median_similarity": 0,
            "similarity_range": 0,
            "high_similarity_ratio": 0,
            "connectivity_score": 0,
        }

    def _perform_method_level_tests(self, method_features: pd.DataFrame) -> Dict:
        """
        メソッドレベルの統計検定を実行

        Args:
            method_features: 特徴量が追加されたDataFrame

        Returns:
            統計検定結果の辞書
        """
        self.logger.info("メソッドレベル統計検定実行中...")

        # 特徴量カラムのリスト
        feature_columns = [
            "high_similarity_count",
            "medium_similarity_count",
            "low_similarity_count",
            "very_low_similarity_count",
            "max_similarity",
            "min_similarity",
            "avg_similarity",
            "std_similarity",
            "median_similarity",
            "similarity_range",
            "high_similarity_ratio",
            "connectivity_score",
        ]

        # 削除されたメソッドと残存メソッドの比較
        test_config = {
            "batch_comparison": {
                "df": method_features,
                "group_column": "is_deleted",
                "value_columns": feature_columns,
                "group1_value": False,
                "group2_value": True,
            }
        }

        statistical_tests = self.run_statistical_tests(test_config)

        self.logger.info(
            f"メソッドレベル統計検定完了: {len(statistical_tests)}個の検定"
        )
        return statistical_tests

    def create_visualizations(
        self, method_features: pd.DataFrame, output_dir: Path
    ) -> None:
        """
        メソッドレベル特徴量の可視化を作成

        Args:
            method_features: 特徴量が追加されたDataFrame
            output_dir: 出力ディレクトリ
        """
        if not self.config.enable_visualization:
            return

        self.logger.info("メソッドレベル特徴量可視化作成中...")

        # 特徴量カラムのリスト
        feature_columns = [
            "high_similarity_count",
            "medium_similarity_count",
            "low_similarity_count",
            "very_low_similarity_count",
            "max_similarity",
            "min_similarity",
            "avg_similarity",
            "std_similarity",
            "median_similarity",
            "similarity_range",
            "high_similarity_ratio",
            "connectivity_score",
        ]

        # 削除されたメソッドと残存メソッドの分布比較
        if "is_deleted" in method_features.columns:
            fig = self.visualizer.create_summary_statistics_plot(
                method_features,
                "is_deleted",
                feature_columns,
                False,  # 残存メソッド
                True,  # 削除メソッド
            )

            self.save_visualization(fig, "method_feature_distribution_comparison.png")

        self.logger.info("メソッドレベル特徴量可視化完了")

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
        self.logger.info("メソッドレベル特徴量分析開始")

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
                            snapshot_results = self.analyze_with_tracing(
                                snapshot_path, tracing_files[0]
                            )
                        else:
                            snapshot_results = self.analyze_snapshot(snapshot_path)
                    else:
                        snapshot_results = self.analyze_snapshot(snapshot_path)

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
                results = self.analyze_all_snapshots(self.config.results_dir)

        # 結果を保存
        self.save_results(results, "method_level_feature_")

        # 要約レポートを作成
        summary_report = self.create_summary_report(results)
        self.save_results({"summary_report": summary_report}, "method_level_feature_")

        # ログ出力
        self.log_analysis_summary(results)

        self.logger.info("メソッドレベル特徴量分析完了")
        return results
