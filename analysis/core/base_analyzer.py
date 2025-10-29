#!/usr/bin/env python3
"""
基底分析クラス

全ての分析器の基底となるクラス。共通機能を提供する。
"""

import logging
from pathlib import Path
from typing import Dict

import pandas as pd
from config.settings import AnalysisConfig
from utils.logging_utils import setup_logging

from core.data_loader import DataLoader
from core.statistical_tester import StatisticalTester
from core.visualizer import Visualizer


class BaseAnalyzer:
    """全ての分析器の基底クラス"""

    def __init__(self, config: AnalysisConfig, analysis_type: str):
        """
        初期化

        Args:
            config: 分析設定
            analysis_type: 分析タイプ（ログファイル名に使用）
        """
        self.config = config
        self.analysis_type = analysis_type

        # ログ設定
        log_file = self.config.get_log_file_path(analysis_type)
        setup_logging(log_file)
        self.logger = logging.getLogger(__name__)

        # 共通コンポーネントの初期化
        self.data_loader = DataLoader(self.logger)
        self.statistical_tester = StatisticalTester(self.logger, self.config)
        self.visualizer = Visualizer(self.logger, self.config)

        # 出力ディレクトリ
        self.output_dir = self.config.get_output_subdir(analysis_type)

        self.logger.info(f"{self.__class__.__name__}初期化完了")

    def load_snapshot_data(self, snapshot_path: Path) -> Dict[str, pd.DataFrame]:
        """
        スナップショットのデータを読み込む

        Args:
            snapshot_path: スナップショットディレクトリのパス

        Returns:
            データの辞書
        """
        self.logger.info(f"スナップショットデータ読み込み: {snapshot_path}")

        data = self.data_loader.load_all_data_for_snapshot(snapshot_path)

        self.logger.info(f"読み込み完了: {list(data.keys())}")
        return data

    def save_results(self, results: Dict, filename_prefix: str = "") -> None:
        """
        結果を保存

        Args:
            results: 保存する結果の辞書
            filename_prefix: ファイル名のプレフィックス
        """
        self.logger.info(f"結果保存開始: {self.output_dir}")

        for key, data in results.items():
            if isinstance(data, pd.DataFrame):
                filename = (
                    f"{filename_prefix}{key}.csv" if filename_prefix else f"{key}.csv"
                )
                filepath = self.output_dir / filename
                data.to_csv(filepath, index=False)
                self.logger.info(f"DataFrame保存: {filepath}")

            elif isinstance(data, dict):
                filename = (
                    f"{filename_prefix}{key}.csv" if filename_prefix else f"{key}.csv"
                )
                filepath = self.output_dir / filename
                df = pd.DataFrame([data])
                df.to_csv(filepath, index=False)
                self.logger.info(f"辞書保存: {filepath}")

        self.logger.info("結果保存完了")

    def save_visualization(self, fig, filename: str) -> None:
        """
        可視化を保存

        Args:
            fig: matplotlib Figure
            filename: ファイル名
        """
        if self.config.enable_visualization:
            filepath = self.output_dir / filename
            self.visualizer.save_figure(fig, filepath)

    def run_statistical_tests(self, test_config: Dict) -> Dict:
        """
        統計検定を実行

        Args:
            test_config: 検定設定の辞書

        Returns:
            検定結果の辞書
        """
        if not self.config.enable_statistical_tests:
            self.logger.info("統計検定は無効化されています")
            return {}

        self.logger.info("統計検定実行中...")

        results = {}

        # 比較検定
        if "comparison_tests" in test_config:
            for test_name, test_params in test_config["comparison_tests"].items():
                result = self.statistical_tester.compare_groups(**test_params)
                results[test_name] = result

        # 相関分析
        if "correlation_tests" in test_config:
            for test_name, test_params in test_config["correlation_tests"].items():
                result = self.statistical_tester.spearman_correlation_test(
                    **test_params
                )
                results[test_name] = result

        # 一括検定
        if "batch_comparison" in test_config:
            batch_results = self.statistical_tester.batch_comparison_tests(
                **test_config["batch_comparison"]
            )
            results.update(batch_results)

        if "batch_correlation" in test_config:
            batch_results = self.statistical_tester.batch_correlation_tests(
                **test_config["batch_correlation"]
            )
            results.update(batch_results)

        # 多重比較補正
        if results:
            results = self.statistical_tester.apply_multiple_comparison_correction(
                results
            )

        self.logger.info(f"統計検定完了: {len(results)}個の検定を実行")
        return results

    def create_summary_report(self, results: Dict) -> Dict:
        """
        要約レポートを作成

        Args:
            results: 分析結果の辞書

        Returns:
            要約レポートの辞書
        """
        summary = {
            "analysis_type": self.analysis_type,
            "timestamp": pd.Timestamp.now().isoformat(),
            "config": {
                "ngram_threshold": self.config.ngram_threshold,
                "lcs_threshold": self.config.lcs_threshold,
                "significance_level": self.config.significance_level,
            },
        }

        # 結果の要約を追加
        for key, data in results.items():
            if isinstance(data, pd.DataFrame):
                summary[f"{key}_count"] = len(data)
                summary[f"{key}_columns"] = list(data.columns)
            elif isinstance(data, dict):
                summary[f"{key}_keys"] = list(data.keys())

        return summary

    def log_analysis_summary(self, results: Dict) -> None:
        """
        分析結果の要約をログ出力

        Args:
            results: 分析結果の辞書
        """
        self.logger.info("=== 分析結果要約 ===")

        for key, data in results.items():
            if isinstance(data, pd.DataFrame):
                self.logger.info(f"{key}: {len(data)}行")
            elif isinstance(data, dict):
                self.logger.info(f"{key}: {len(data)}項目")

        self.logger.info("=== 分析完了 ===")
