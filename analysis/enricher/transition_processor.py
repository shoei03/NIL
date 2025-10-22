#!/usr/bin/env python3
"""
Transition Processor

遷移ディレクトリの処理を行うクラス。
"""

import logging
from pathlib import Path
from typing import List

import pandas as pd

from .method_tracing_loader import MethodTracingLoader
from .pair_classifier import PairClassifier
from .statistics_collector import StatisticsCollector


class TransitionProcessor:
    """遷移ディレクトリの処理を行うクラス"""

    def __init__(self, similarity_threshold: float = 0.75):
        """
        初期化

        Args:
            similarity_threshold: high_risk判定の類似度閾値
        """
        self.method_loader = MethodTracingLoader()
        self.classifier = PairClassifier(similarity_threshold)
        self.statistics = StatisticsCollector()

    def find_transition_directories(self, output_dir: Path) -> List[Path]:
        """
        遷移ディレクトリを検索

        Args:
            output_dir: 出力ディレクトリ（遷移ディレクトリの親）

        Returns:
            遷移ディレクトリのリスト
        """
        # ディレクトリ名パターン: YYYYMMDD_HHMMSS_hash_to_YYYYMMDD_HHMMSS_hash
        transition_dirs = []
        for item in output_dir.iterdir():
            if item.is_dir() and "_to_" in item.name:
                transition_dirs.append(item)
        return sorted(transition_dirs)

    def _enrich_pairs(
        self, input_path: Path, output_path: Path, pair_type: str
    ) -> None:
        """
        ペアCSVをエンリッチして出力

        Args:
            input_path: 入力CSVパス (added.csv, deleted.csv, persisted.csv)
            output_path: 出力CSVパス (*_enriched.csv)
            pair_type: 'added', 'deleted', 'persisted'のいずれか
        """
        try:
            df = pd.read_csv(input_path)
        except FileNotFoundError:
            logging.warning(f"File not found, skipping: {input_path}")
            return
        except Exception as e:
            logging.error(f"Error reading {input_path}: {e}")
            return

        # 空のファイルの場合
        if df.empty:
            logging.info(f"  {input_path.name}: empty file")
            # ヘッダーのみの出力ファイルを生成
            enriched_df = pd.DataFrame(
                columns=[
                    "method_a",
                    "method_b",
                    "change_category",
                    "method_a_change_type",
                    "method_b_change_type",
                    "method_a_similarity",
                    "method_b_similarity",
                ]
            )
            enriched_df.to_csv(output_path, index=False)
            return

        # 必須カラムのチェック
        if "method_a" not in df.columns or "method_b" not in df.columns:
            logging.error(
                f"{input_path.name} is missing required columns: method_a, method_b"
            )
            return

        # エンリッチメント情報を追加
        enriched_rows = []
        for _, row in df.iterrows():
            method_a = str(row["method_a"])
            method_b = str(row["method_b"])

            # 各メソッドの変更情報を取得
            change_a, similarity_a = self.method_loader.get_method_info(method_a)
            change_b, similarity_b = self.method_loader.get_method_info(method_b)

            # カテゴリを分類
            if pair_type == "deleted":
                category = self.classifier.classify_deleted_pair(change_a, change_b)
            elif pair_type == "added":
                category = self.classifier.classify_added_pair(change_a, change_b)
            elif pair_type == "persisted":
                category = self.classifier.classify_persisted_pair(
                    change_a, change_b, similarity_a, similarity_b
                )
            else:
                category = "unknown"

            # 統計情報を更新
            self.statistics.add_statistic(pair_type, category)

            enriched_rows.append(
                {
                    "method_a": method_a,
                    "method_b": method_b,
                    "change_category": category,
                    "method_a_change_type": change_a,
                    "method_b_change_type": change_b,
                    "method_a_similarity": similarity_a
                    if similarity_a is not None
                    else "",
                    "method_b_similarity": similarity_b
                    if similarity_b is not None
                    else "",
                }
            )

        # 出力
        enriched_df = pd.DataFrame(enriched_rows)
        enriched_df.to_csv(output_path, index=False)
        logging.info(
            f"  {input_path.name}: {len(enriched_rows)} pairs -> {output_path.name}"
        )

    def process_transition_directory(self, transition_dir: Path) -> None:
        """
        遷移ディレクトリを処理

        Args:
            transition_dir: 遷移ディレクトリのパス
        """
        logging.info(f"Processing transition: {transition_dir.name}")

        # この遷移ディレクトリ内のmethod_tracing.csvを読み込み
        method_tracing_path = transition_dir / "method_tracing.csv"
        if not method_tracing_path.exists():
            logging.warning(
                f"  method_tracing.csv not found in {transition_dir.name}, skipping"
            )
            return

        self.method_loader.load_method_tracing(method_tracing_path)

        # method_tracing.csvが正しく読み込めなかった場合はスキップ
        if not self.method_loader.is_loaded():
            logging.warning("  Failed to load method_tracing.csv, skipping transition")
            return

        # added.csv -> added_enriched.csv
        added_path = transition_dir / "added.csv"
        added_enriched_path = transition_dir / "added_enriched.csv"
        self._enrich_pairs(added_path, added_enriched_path, "added")

        # deleted.csv -> deleted_enriched.csv
        deleted_path = transition_dir / "deleted.csv"
        deleted_enriched_path = transition_dir / "deleted_enriched.csv"
        self._enrich_pairs(deleted_path, deleted_enriched_path, "deleted")

        # persisted.csv -> persisted_enriched.csv
        persisted_path = transition_dir / "persisted.csv"
        persisted_enriched_path = transition_dir / "persisted_enriched.csv"
        self._enrich_pairs(persisted_path, persisted_enriched_path, "persisted")
