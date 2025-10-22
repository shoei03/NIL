#!/usr/bin/env python3
"""
Statistics Collector

統計情報の収集と管理を行うクラス。
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import pandas as pd

from .exceptions import StatisticsError
from .interfaces import StatisticsCollectorInterface


class StatisticsCollector(StatisticsCollectorInterface):
    """統計情報の収集と管理を行うクラス"""

    def __init__(self):
        """初期化"""
        self.statistics = {
            "added": defaultdict(int),
            "deleted": defaultdict(int),
            "persisted": defaultdict(int),
        }

    def add_statistic(self, pair_type: str, category: str) -> None:
        """
        統計情報を追加

        Args:
            pair_type: ペアタイプ ('added', 'deleted', 'persisted')
            category: 分類カテゴリ
        """
        if pair_type not in self.statistics:
            raise StatisticsError(
                f"Invalid pair_type: {pair_type}. Must be one of: added, deleted, persisted",
                pair_type=pair_type,
            )

        try:
            self.statistics[pair_type][category] += 1
        except Exception as e:
            raise StatisticsError(
                f"Failed to add statistic for {pair_type}:{category}",
                pair_type=pair_type,
                category=category,
                details=str(e),
            ) from e

    def get_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        統計情報を取得

        Returns:
            統計情報の辞書
        """
        return dict(self.statistics)

    def log_statistics(self) -> None:
        """統計情報をログに出力"""
        logging.info("Statistics:")
        for pair_type, categories in self.statistics.items():
            if categories:
                stats_str = ", ".join(
                    [f"{cat}={count}" for cat, count in sorted(categories.items())]
                )
                logging.info(f"  {pair_type}: {stats_str}")

    def get_transition_statistics(self, output_dir: Path) -> List[Dict]:
        """
        各遷移ディレクトリの個別統計を取得

        Args:
            output_dir: 出力ディレクトリ（pair_diff_with_lists）

        Returns:
            各遷移の統計情報のリスト
        """
        transition_stats = []

        # 遷移ディレクトリを検索
        for item in output_dir.iterdir():
            if item.is_dir() and "_to_" in item.name:
                transition_name = item.name

                # 各遷移ディレクトリの統計を計算
                transition_stat = {
                    "transition": transition_name,
                    "added": defaultdict(int),
                    "deleted": defaultdict(int),
                    "persisted": defaultdict(int),
                }

                # 各ペアタイプのCSVファイルを処理
                for pair_type in ["added", "deleted", "persisted"]:
                    enriched_file = item / f"{pair_type}_enriched.csv"
                    if enriched_file.exists():
                        try:
                            df = pd.read_csv(enriched_file)
                            if not df.empty and "change_category" in df.columns:
                                category_counts = df["change_category"].value_counts()
                                for category, count in category_counts.items():
                                    transition_stat[pair_type][category] = int(count)
                        except Exception as e:
                            logging.warning(f"Error reading {enriched_file}: {e}")

                transition_stats.append(transition_stat)

        return transition_stats

    def save_transition_statistics(self, output_dir: Path) -> None:
        """
        各遷移ディレクトリの統計情報をCSVファイルに保存

        Args:
            output_dir: 出力ディレクトリ（pair_diff_with_lists）
        """
        transition_stats = self.get_transition_statistics(output_dir)

        # CSVデータを準備
        csv_data = []
        for stat in transition_stats:
            transition = stat["transition"]

            # 各ペアタイプとカテゴリの組み合わせを処理
            for pair_type in ["added", "deleted", "persisted"]:
                for category, count in stat[pair_type].items():
                    csv_data.append(
                        {
                            "transition": transition,
                            "pair_type": pair_type,
                            "change_category": category,
                            "count": count,
                        }
                    )

        # CSVファイルに保存
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_path = output_dir / "pair_enrichment_statistics.csv"
            df.to_csv(csv_path, index=False)
            logging.info(f"Pair enrichment statistics saved to: {csv_path}")

    def save_statistics_summary(self, output_dir: Path) -> None:
        """
        統計サマリーをpair_diff_with_lists直下に保存

        Args:
            output_dir: 出力ディレクトリ（pair_diff_with_lists）
        """
        transition_stats = self.get_transition_statistics(output_dir)

        # 全体統計を計算
        total_stats = {
            "added": defaultdict(int),
            "deleted": defaultdict(int),
            "persisted": defaultdict(int),
        }

        for stat in transition_stats:
            for pair_type in ["added", "deleted", "persisted"]:
                for category, count in stat[pair_type].items():
                    total_stats[pair_type][category] += count

        # サマリーCSVデータを準備
        summary_data = []
        for pair_type, categories in total_stats.items():
            for category, count in categories.items():
                summary_data.append(
                    {
                        "pair_type": pair_type,
                        "change_category": category,
                        "total_count": count,
                    }
                )

        # サマリーファイルに保存
        if summary_data:
            df = pd.DataFrame(summary_data)
            summary_path = output_dir / "pair_enrichment_summary.csv"
            df.to_csv(summary_path, index=False)
            logging.info(f"Pair enrichment summary saved to: {summary_path}")

            # ログにも出力
            logging.info("Statistics Summary:")
            for pair_type, categories in total_stats.items():
                if categories:
                    stats_str = ", ".join(
                        [f"{cat}={count}" for cat, count in sorted(categories.items())]
                    )
                    logging.info(f"  {pair_type}: {stats_str}")

    def reset(self) -> None:
        """統計情報をリセット"""
        self.statistics = {
            "added": defaultdict(int),
            "deleted": defaultdict(int),
            "persisted": defaultdict(int),
        }
