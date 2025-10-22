#!/usr/bin/env python3
"""
Pair Enricher

クローンペアにエンリッチメント情報を付加するメインクラス。
"""

import logging
from pathlib import Path

from .transition_processor import TransitionProcessor


class PairEnricher:
    """クローンペアにエンリッチメント情報を付加するメインクラス"""

    def __init__(self, output_dir: Path, similarity_threshold: float = 0.75):
        """
        初期化

        Args:
            output_dir: 出力ディレクトリ（遷移ディレクトリの親）
            similarity_threshold: high_risk判定の類似度閾値
        """
        self.output_dir = output_dir
        self.processor = TransitionProcessor(similarity_threshold)

    def run(self) -> None:
        """メイン処理を実行"""
        logging.info("Starting pair enrichment")

        # 遷移ディレクトリを走査
        transition_dirs = self.processor.find_transition_directories(self.output_dir)
        if not transition_dirs:
            logging.warning(f"No transition directories found in {self.output_dir}")
            return

        logging.info(f"Found {len(transition_dirs)} transition directories")

        # 各遷移ディレクトリを処理
        for transition_dir in transition_dirs:
            self.processor.process_transition_directory(transition_dir)

        # 統計情報を出力
        logging.info(f"Completed: {len(transition_dirs)} transitions processed")

        # 各遷移ディレクトリの統計情報を保存
        self.processor.statistics.save_transition_statistics(self.output_dir)

        # 統計サマリーを保存
        self.processor.statistics.save_statistics_summary(self.output_dir)
