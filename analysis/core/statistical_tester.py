#!/usr/bin/env python3
"""
統計検定統一モジュール

全ての分析器で使用する統計検定処理を統一管理する。
"""

import logging
from typing import Dict, List

import pandas as pd
from config.settings import StatisticalTestConfig
from scipy.stats import mannwhitneyu, spearmanr


class StatisticalTester:
    """統計検定の統一処理"""

    def __init__(self, logger: logging.Logger, config: StatisticalTestConfig):
        """
        初期化

        Args:
            logger: ログ出力用のlogger
            config: 統計検定の設定
        """
        self.logger = logger
        self.config = config

    def mann_whitney_u_test(
        self, group1: pd.Series, group2: pd.Series, test_name: str = "Mann-Whitney U"
    ) -> Dict:
        """
        Mann-Whitney U検定を実行

        Args:
            group1: 第1群のデータ
            group2: 第2群のデータ
            test_name: 検定名

        Returns:
            検定結果の辞書
        """
        try:
            test_result = mannwhitneyu(
                group1, group2, alternative=self.config.alternative
            )

            return {
                "test": test_name,
                "statistic": test_result.statistic,
                "p_value": test_result.pvalue,
                "group1_mean": group1.mean(),
                "group2_mean": group2.mean(),
                "group1_median": group1.median(),
                "group2_median": group2.median(),
                "is_significant": test_result.pvalue < self.config.significance_level,
            }
        except Exception as e:
            self.logger.warning(f"Mann-Whitney U検定エラー: {e}")
            return {
                "test": test_name,
                "statistic": None,
                "p_value": None,
                "error": str(e),
            }

    def spearman_correlation_test(
        self, x: pd.Series, y: pd.Series, test_name: str = "Spearman correlation"
    ) -> Dict:
        """
        Spearman相関分析を実行

        Args:
            x: 第1変数
            y: 第2変数
            test_name: 検定名

        Returns:
            相関分析結果の辞書
        """
        try:
            correlation_result = spearmanr(x, y)

            return {
                "test": test_name,
                "correlation": correlation_result.correlation,
                "p_value": correlation_result.pvalue,
                "is_significant": correlation_result.pvalue
                < self.config.significance_level,
                "strength": self._interpret_correlation_strength(
                    abs(correlation_result.correlation)
                ),
            }
        except Exception as e:
            self.logger.warning(f"Spearman相関分析エラー: {e}")
            return {
                "test": test_name,
                "correlation": None,
                "p_value": None,
                "error": str(e),
            }

    def compare_groups(
        self,
        df: pd.DataFrame,
        group_column: str,
        value_column: str,
        group1_value: str,
        group2_value: str,
    ) -> Dict:
        """
        2つのグループを比較

        Args:
            df: データフレーム
            group_column: グループを表すカラム名
            value_column: 比較する値のカラム名
            group1_value: 第1群の値
            group2_value: 第2群の値

        Returns:
            比較結果の辞書
        """
        group1_data = df[df[group_column] == group1_value][value_column]
        group2_data = df[df[group_column] == group2_value][value_column]

        return self.mann_whitney_u_test(
            group1_data, group2_data, f"{group1_value} vs {group2_value}"
        )

    def batch_comparison_tests(
        self,
        df: pd.DataFrame,
        group_column: str,
        value_columns: List[str],
        group1_value: str,
        group2_value: str,
    ) -> Dict[str, Dict]:
        """
        複数の変数について一括で比較検定を実行

        Args:
            df: データフレーム
            group_column: グループを表すカラム名
            value_columns: 比較する値のカラム名のリスト
            group1_value: 第1群の値
            group2_value: 第2群の値

        Returns:
            各変数の比較結果の辞書
        """
        results = {}

        for column in value_columns:
            if column in df.columns:
                results[f"{column}_comparison"] = self.compare_groups(
                    df, group_column, column, group1_value, group2_value
                )

        return results

    def batch_correlation_tests(
        self, df: pd.DataFrame, x_columns: List[str], y_column: str
    ) -> Dict[str, Dict]:
        """
        複数の変数について一括で相関分析を実行

        Args:
            df: データフレーム
            x_columns: 独立変数のカラム名のリスト
            y_column: 従属変数のカラム名

        Returns:
            各変数の相関分析結果の辞書
        """
        results = {}

        for x_column in x_columns:
            if x_column in df.columns and y_column in df.columns:
                results[f"{x_column}_correlation"] = self.spearman_correlation_test(
                    df[x_column], df[y_column], f"{x_column} vs {y_column}"
                )

        return results

    def apply_multiple_comparison_correction(
        self, test_results: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        """
        多重比較補正を適用

        Args:
            test_results: 検定結果の辞書

        Returns:
            補正後の検定結果の辞書
        """
        if not self.config.enable_bonferroni_correction:
            return test_results

        num_tests = len(
            [
                r
                for r in test_results.values()
                if "p_value" in r and r["p_value"] is not None
            ]
        )
        corrected_alpha = self.config.get_corrected_alpha(num_tests)

        corrected_results = {}
        for test_name, result in test_results.items():
            corrected_result = result.copy()
            if "p_value" in result and result["p_value"] is not None:
                corrected_result["corrected_alpha"] = corrected_alpha
                corrected_result["is_significant_corrected"] = (
                    result["p_value"] < corrected_alpha
                )
            corrected_results[test_name] = corrected_result

        return corrected_results

    def _interpret_correlation_strength(self, correlation: float) -> str:
        """相関の強さを解釈"""
        if correlation < 0.1:
            return "negligible"
        elif correlation < 0.3:
            return "weak"
        elif correlation < 0.5:
            return "moderate"
        elif correlation < 0.7:
            return "strong"
        else:
            return "very strong"
