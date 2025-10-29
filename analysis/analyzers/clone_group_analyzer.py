#!/usr/bin/env python3
"""
クローングループ分析器（統合版）

クローンペアからグラフ理論の連結成分を用いてクローンのグループを作成し、
code_blocks.csvにグループ情報を追加する。
"""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from config.settings import AnalysisConfig
from core.base_analyzer import BaseAnalyzer
from core.graph_utils import GraphUtils
from tqdm import tqdm


class CloneGroupAnalyzer(BaseAnalyzer):
    """クローングループ分析器"""

    def __init__(self, config: AnalysisConfig):
        """
        初期化

        Args:
            config: 分析設定
        """
        super().__init__(config, "clone_group")

        # グラフユーティリティの初期化
        self.graph_utils = GraphUtils(self.logger)

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

        if "clone_pairs" not in data or "code_blocks" not in data:
            self.logger.warning(f"必要なデータが見つかりません: {snapshot_path}")
            return {}

        clone_pairs_df = data["clone_pairs"]
        code_blocks_df = data["code_blocks"]

        # グラフ構築
        self.logger.info("グラフ構築中...")
        graph = self.graph_utils.build_graph_from_pairs(
            clone_pairs_df, self.config.ngram_threshold, self.config.lcs_threshold
        )

        # 連結成分検出
        self.logger.info("連結成分検出中...")
        components = self.graph_utils.find_connected_components(graph)

        # 統計計算
        stats = self.graph_utils.calculate_component_statistics(components, graph)
        self.logger.info(f"統計情報: {stats}")

        # グループマッピング作成
        group_mapping = self.graph_utils.create_group_mapping(components)
        group_similarities = self.graph_utils.calculate_group_similarities(
            components, graph
        )

        # code_blocksにグループ情報を追加
        enhanced_code_blocks = self._enhance_code_blocks(
            code_blocks_df, group_mapping, group_similarities
        )

        # 結果をまとめる
        results = {
            "enhanced_code_blocks": enhanced_code_blocks,
            "component_statistics": pd.DataFrame([stats]),
        }

        self.logger.info(f"スナップショット分析完了: {snapshot_path}")
        return results

    def analyze_all_snapshots(self, results_dir: Path) -> Dict[str, pd.DataFrame]:
        """
        全スナップショットを分析

        Args:
            results_dir: resultsディレクトリのパス

        Returns:
            全スナップショットの分析結果
        """
        self.logger.info(f"全スナップショット分析開始: {results_dir}")

        snapshot_dirs = [d for d in results_dir.iterdir() if d.is_dir()]
        snapshot_dirs.sort()

        all_results = {}
        summary_stats = []

        for snapshot_dir in tqdm(snapshot_dirs, desc="スナップショット分析"):
            try:
                snapshot_results = self.analyze_snapshot(snapshot_dir)

                if snapshot_results:
                    # 個別結果を保存
                    snapshot_name = snapshot_dir.name
                    all_results[snapshot_name] = snapshot_results

                    # 統計情報を収集
                    if "component_statistics" in snapshot_results:
                        stats_df = snapshot_results["component_statistics"].copy()
                        stats_df["snapshot"] = snapshot_name
                        summary_stats.append(stats_df)

            except Exception as e:
                self.logger.error(f"スナップショット分析エラー {snapshot_dir}: {e}")
                continue

        # 全スナップショットの統計をまとめる
        if summary_stats:
            all_results["summary_statistics"] = pd.concat(
                summary_stats, ignore_index=True
            )

        self.logger.info(
            f"全スナップショット分析完了: {len(all_results)}個のスナップショット"
        )
        return all_results

    def _enhance_code_blocks(
        self,
        code_blocks_df: pd.DataFrame,
        group_mapping: Dict[str, int],
        group_similarities: Dict[int, float],
    ) -> pd.DataFrame:
        """
        code_blocksにグループ情報を追加

        Args:
            code_blocks_df: 元のcode_blocks DataFrame
            group_mapping: ノードID -> グループID のマッピング
            group_similarities: グループID -> 平均類似度 のマッピング

        Returns:
            拡張されたcode_blocks DataFrame
        """
        enhanced_df = code_blocks_df.copy()

        # グループ情報を追加
        enhanced_df["group_id"] = (
            enhanced_df["token_hash"].map(group_mapping).fillna(-1).astype(int)
        )
        enhanced_df["group_size"] = enhanced_df["group_id"].map(
            lambda gid: len([k for k, v in group_mapping.items() if v == gid])
            if gid != -1
            else 0
        )
        enhanced_df["avg_similarity"] = (
            enhanced_df["group_id"].map(group_similarities).fillna(0.0)
        )

        # グループに属さないブロックの処理
        enhanced_df.loc[enhanced_df["group_id"] == -1, "group_size"] = 1
        enhanced_df.loc[enhanced_df["group_id"] == -1, "avg_similarity"] = 0.0

        self.logger.info(f"コードブロック拡張完了: {len(enhanced_df)}個のブロック")
        return enhanced_df

    def save_enhanced_code_blocks(
        self, enhanced_df: pd.DataFrame, snapshot_path: Path
    ) -> None:
        """
        拡張されたcode_blocksを保存

        Args:
            enhanced_df: 拡張されたcode_blocks DataFrame
            snapshot_path: スナップショットディレクトリのパス
        """
        output_path = snapshot_path / "code_blocks_enhanced.csv"
        enhanced_df.to_csv(output_path, index=False)
        self.logger.info(f"拡張code_blocks保存: {output_path}")

    def run_analysis(
        self, target_snapshots: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        分析を実行

        Args:
            target_snapshots: 対象スナップショットのリスト（Noneの場合は全スナップショット）

        Returns:
            分析結果の辞書
        """
        self.logger.info("クローングループ分析開始")

        if target_snapshots:
            # 指定されたスナップショットのみ分析
            results = {}
            for snapshot_name in target_snapshots:
                snapshot_path = self.config.results_dir / snapshot_name
                if snapshot_path.exists():
                    snapshot_results = self.analyze_snapshot(snapshot_path)
                    if snapshot_results:
                        results[snapshot_name] = snapshot_results
                else:
                    self.logger.warning(
                        f"スナップショットが見つかりません: {snapshot_name}"
                    )
        else:
            # 全スナップショットを分析
            results = self.analyze_all_snapshots(self.config.results_dir)

        # 結果を保存
        self.save_results(results, "clone_group_")

        # 要約レポートを作成
        summary_report = self.create_summary_report(results)
        self.save_results({"summary_report": summary_report}, "clone_group_")

        # ログ出力
        self.log_analysis_summary(results)

        self.logger.info("クローングループ分析完了")
        return results
