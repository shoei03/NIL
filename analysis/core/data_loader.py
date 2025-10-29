#!/usr/bin/env python3
"""
データ読み込み統一モジュール

全ての分析器で使用するデータ読み込み処理を統一管理する。
"""

import logging
from pathlib import Path
from typing import Dict, Set

import pandas as pd


class DataLoader:
    """データ読み込みの統一処理"""

    def __init__(self, logger: logging.Logger):
        """
        初期化

        Args:
            logger: ログ出力用のlogger
        """
        self.logger = logger

    def load_enhanced_code_blocks(self, csv_path: Path) -> pd.DataFrame:
        """拡張されたcode_blocks.csvを読み込む"""
        self.logger.info(f"code_blocks_enhanced.csv読み込み: {csv_path}")

        df = pd.read_csv(
            csv_path,
            header=None,
            names=[
                "token_hash",
                "file_path",
                "start_line",
                "end_line",
                "method_name",
                "return_type",
                "parameters",
                "commit_hash",
                "token_sequence",
                "group_id",
                "group_size",
                "avg_similarity",
            ],
        )

        self.logger.info(f"読み込み完了: {len(df)}個のコードブロック")
        return df

    def load_code_blocks(self, csv_path: Path) -> pd.DataFrame:
        """通常のcode_blocks.csvを読み込む"""
        self.logger.info(f"code_blocks.csv読み込み: {csv_path}")

        df = pd.read_csv(
            csv_path,
            header=None,
            names=[
                "token_hash",
                "file_path",
                "start_line",
                "end_line",
                "method_name",
                "return_type",
                "parameters",
                "commit_hash",
                "token_sequence",
            ],
        )

        self.logger.info(f"読み込み完了: {len(df)}個のコードブロック")
        return df

    def load_method_tracing(self, csv_path: Path) -> pd.DataFrame:
        """method_tracing.csvを読み込む"""
        self.logger.info(f"method_tracing.csv読み込み: {csv_path}")

        df = pd.read_csv(csv_path)

        self.logger.info(f"読み込み完了: {len(df)}個の追跡レコード")
        return df

    def load_clone_pairs(self, csv_path: Path) -> pd.DataFrame:
        """clone_pairs.csvを読み込む"""
        self.logger.info(f"clone_pairs.csv読み込み: {csv_path}")

        df = pd.read_csv(
            csv_path,
            header=None,
            names=["block_id1", "block_id2", "ngram_similarity", "lcs_similarity"],
        )

        # データ型の変換
        df["ngram_similarity"] = pd.to_numeric(df["ngram_similarity"], errors="coerce")
        df["lcs_similarity"] = pd.to_numeric(df["lcs_similarity"], errors="coerce")

        # 欠損値の処理
        df = df.dropna(subset=["block_id1", "block_id2", "ngram_similarity"])

        self.logger.info(f"読み込み完了: {len(df)}個のペア")
        return df

    def identify_deleted_methods(self, tracing_df: pd.DataFrame) -> Set[str]:
        """削除されたメソッドのtoken_hashを特定"""
        deleted_methods = set()

        for _, row in tracing_df.iterrows():
            if row["change_type"] == "deleted" and pd.notna(row["method_t_token_hash"]):
                deleted_methods.add(str(row["method_t_token_hash"]))

        self.logger.info(f"削除されたメソッド数: {len(deleted_methods)}")
        return deleted_methods

    def get_effective_similarity(self, ngram_sim: float, lcs_sim: float) -> float:
        """有効な類似度を決定する"""
        if lcs_sim is not None and not pd.isna(lcs_sim) and lcs_sim != "":
            return float(lcs_sim)
        else:
            return float(ngram_sim)

    def load_all_data_for_snapshot(
        self, snapshot_path: Path
    ) -> Dict[str, pd.DataFrame]:
        """スナップショットの全データを読み込む"""
        data = {}

        # ファイルパスの確認
        clone_pairs_path = snapshot_path / "clone_pairs.csv"
        code_blocks_path = snapshot_path / "code_blocks.csv"
        enhanced_code_blocks_path = snapshot_path / "code_blocks_enhanced.csv"

        # データ読み込み
        if clone_pairs_path.exists():
            data["clone_pairs"] = self.load_clone_pairs(clone_pairs_path)

        if code_blocks_path.exists():
            data["code_blocks"] = self.load_code_blocks(code_blocks_path)

        if enhanced_code_blocks_path.exists():
            data["enhanced_code_blocks"] = self.load_enhanced_code_blocks(
                enhanced_code_blocks_path
            )

        return data
