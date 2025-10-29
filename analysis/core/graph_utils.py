#!/usr/bin/env python3
"""
グラフ操作ユーティリティ（統合版）

クローンペアからグラフを構築し、連結成分を検出するためのユーティリティ関数を提供する。
"""

import logging
from typing import Dict, List, Optional, Set

import networkx as nx
import pandas as pd


class GraphUtils:
    """グラフ操作のためのユーティリティクラス"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初期化

        Args:
            logger: ログ出力用のlogger（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)

    def build_graph_from_pairs(
        self, pairs_df: pd.DataFrame, ngram_threshold: int = 50, lcs_threshold: int = 60
    ) -> nx.Graph:
        """
        クローンペアのDataFrameからグラフを構築する

        Args:
            pairs_df: クローンペアのDataFrame
                     columns: ['block_id1', 'block_id2', 'ngram_similarity', 'lcs_similarity']
            ngram_threshold: N-gram類似度の閾値（0-100）
            lcs_threshold: LCS類似度の閾値（0-100）

        Returns:
            構築されたグラフ（NetworkX Graph）
        """
        graph = nx.Graph()
        added_edges = 0
        filtered_edges = 0

        for _, row in pairs_df.iterrows():
            block_id1 = row["block_id1"]
            block_id2 = row["block_id2"]
            ngram_sim = row["ngram_similarity"]
            lcs_sim = row["lcs_similarity"]

            # 有効な類似度を決定
            effective_similarity = self._get_effective_similarity(ngram_sim, lcs_sim)

            # 閾値チェック
            if self._meets_threshold(
                effective_similarity, ngram_sim, lcs_sim, ngram_threshold, lcs_threshold
            ):
                graph.add_edge(block_id1, block_id2, similarity=effective_similarity)
                added_edges += 1
            else:
                filtered_edges += 1

        self.logger.info(
            f"グラフ構築完了: {added_edges}個のエッジを追加, {filtered_edges}個をフィルタリング"
        )
        return graph

    def find_connected_components(self, graph: nx.Graph) -> List[Set[str]]:
        """
        グラフの連結成分を検出する

        Args:
            graph: NetworkX Graph

        Returns:
            連結成分のリスト（各成分はノードIDのセット）
        """
        components = list(nx.connected_components(graph))
        self.logger.info(f"連結成分検出完了: {len(components)}個の成分")
        return components

    def calculate_component_statistics(
        self, components: List[Set[str]], graph: nx.Graph
    ) -> Dict[str, float]:
        """
        連結成分の統計を計算する

        Args:
            components: 連結成分のリスト
            graph: 元のグラフ

        Returns:
            統計情報の辞書
        """
        if not components:
            return {"avg_size": 0, "max_size": 0, "min_size": 0, "total_nodes": 0}

        sizes = [len(component) for component in components]

        return {
            "avg_size": sum(sizes) / len(sizes),
            "max_size": max(sizes),
            "min_size": min(sizes),
            "total_nodes": sum(sizes),
            "num_components": len(components),
        }

    def create_group_mapping(self, components: List[Set[str]]) -> Dict[str, int]:
        """
        ノードIDからグループIDへのマッピングを作成する

        Args:
            components: 連結成分のリスト

        Returns:
            ノードID -> グループID の辞書
        """
        group_mapping = {}

        for group_id, component in enumerate(components):
            for node_id in component:
                group_mapping[node_id] = group_id

        self.logger.info(f"グループマッピング作成完了: {len(group_mapping)}個のノード")
        return group_mapping

    def calculate_group_similarities(
        self, components: List[Set[str]], graph: nx.Graph
    ) -> Dict[int, float]:
        """
        各グループの平均類似度を計算する

        Args:
            components: 連結成分のリスト
            graph: 元のグラフ

        Returns:
            グループID -> 平均類似度 の辞書
        """
        group_similarities = {}

        for group_id, component in enumerate(components):
            similarities = []

            # グループ内の全てのエッジの類似度を収集
            for node1 in component:
                for node2 in component:
                    if node1 != node2 and graph.has_edge(node1, node2):
                        similarity = graph[node1][node2].get("similarity", 0)
                        similarities.append(similarity)

            # 平均類似度を計算
            if similarities:
                group_similarities[group_id] = sum(similarities) / len(similarities)
            else:
                group_similarities[group_id] = 0.0

        self.logger.info(
            f"グループ類似度計算完了: {len(group_similarities)}個のグループ"
        )
        return group_similarities

    def _get_effective_similarity(self, ngram_sim: float, lcs_sim: float) -> float:
        """有効な類似度を決定する"""
        if lcs_sim is not None and not pd.isna(lcs_sim) and lcs_sim != "":
            return float(lcs_sim)
        else:
            return float(ngram_sim)

    def _meets_threshold(
        self,
        effective_sim: float,
        ngram_sim: float,
        lcs_sim: float,
        ngram_threshold: int,
        lcs_threshold: int,
    ) -> bool:
        """閾値を満たすかチェックする"""
        # N-gram類似度が閾値を超えている場合
        if ngram_sim >= ngram_threshold:
            return True

        # N-gram類似度が閾値を下回り、LCS類似度が閾値を超えている場合
        if lcs_sim is not None and not pd.isna(lcs_sim) and lcs_sim != "":
            return float(lcs_sim) >= lcs_threshold

        return False
