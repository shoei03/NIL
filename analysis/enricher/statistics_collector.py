#!/usr/bin/env python3
"""
Statistics Collector

統計情報の収集と管理を行うクラス。
"""

import logging
from collections import defaultdict
from typing import Dict

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

    def reset(self) -> None:
        """統計情報をリセット"""
        self.statistics = {
            "added": defaultdict(int),
            "deleted": defaultdict(int),
            "persisted": defaultdict(int),
        }
