#!/usr/bin/env python3
"""
可視化統一モジュール

全ての分析器で使用する可視化処理を統一管理する。
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
from config.settings import AnalysisConfig


class Visualizer:
    """可視化の統一処理"""

    def __init__(self, logger: logging.Logger, config: AnalysisConfig):
        """
        初期化

        Args:
            logger: ログ出力用のlogger
            config: 分析設定
        """
        self.logger = logger
        self.config = config

        # matplotlibの設定
        plt.style.use("default")
        plt.rcParams["figure.figsize"] = self.config.figure_size
        plt.rcParams["figure.dpi"] = self.config.dpi

    def create_distribution_comparison(
        self,
        data1: pd.Series,
        data2: pd.Series,
        labels: Tuple[str, str],
        title: str,
        xlabel: str,
        ylabel: str = "Frequency",
    ) -> plt.Figure:
        """
        2つの分布の比較ヒストグラムを作成

        Args:
            data1: 第1群のデータ
            data2: 第2群のデータ
            labels: 凡例ラベル
            title: タイトル
            xlabel: X軸ラベル
            ylabel: Y軸ラベル

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)

        ax.hist(
            [data1, data2], bins=self.config.bins, alpha=self.config.alpha, label=labels
        )

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()

        return fig

    def create_scatter_plot(
        self,
        x: pd.Series,
        y: pd.Series,
        title: str,
        xlabel: str,
        ylabel: str,
        alpha: float = None,
    ) -> plt.Figure:
        """
        散布図を作成

        Args:
            x: X軸のデータ
            y: Y軸のデータ
            title: タイトル
            xlabel: X軸ラベル
            ylabel: Y軸ラベル
            alpha: 透明度

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)

        ax.scatter(x, y, alpha=alpha or self.config.alpha)

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

        return fig

    def create_multi_panel_plot(
        self, plots_config: List[Dict], title: str = None
    ) -> plt.Figure:
        """
        複数パネルのプロットを作成

        Args:
            plots_config: 各パネルの設定辞書のリスト
            title: 全体のタイトル

        Returns:
            matplotlib Figure
        """
        n_plots = len(plots_config)
        n_cols = min(3, n_plots)
        n_rows = (n_plots + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=self.config.figure_size)

        # 単一パネルの場合は配列に変換
        if n_plots == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes
        else:
            axes = axes.flatten()

        for i, plot_config in enumerate(plots_config):
            ax = axes[i]

            plot_type = plot_config.get("type", "hist")

            if plot_type == "hist":
                self._create_histogram_panel(ax, plot_config)
            elif plot_type == "scatter":
                self._create_scatter_panel(ax, plot_config)
            elif plot_type == "box":
                self._create_boxplot_panel(ax, plot_config)

        # 未使用のパネルを非表示
        for i in range(n_plots, len(axes)):
            axes[i].set_visible(False)

        if title:
            fig.suptitle(title, fontsize=16)

        plt.tight_layout()
        return fig

    def _create_histogram_panel(self, ax: plt.Axes, config: Dict) -> None:
        """ヒストグラムパネルを作成"""
        data = config.get("data", [])
        labels = config.get("labels", [])

        ax.hist(data, bins=self.config.bins, alpha=self.config.alpha, label=labels)

        ax.set_xlabel(config.get("xlabel", ""))
        ax.set_ylabel(config.get("ylabel", "Frequency"))
        ax.set_title(config.get("title", ""))

        if labels:
            ax.legend()

    def _create_scatter_panel(self, ax: plt.Axes, config: Dict) -> None:
        """散布図パネルを作成"""
        x = config.get("x")
        y = config.get("y")

        ax.scatter(x, y, alpha=self.config.alpha)

        ax.set_xlabel(config.get("xlabel", ""))
        ax.set_ylabel(config.get("ylabel", ""))
        ax.set_title(config.get("title", ""))

    def _create_boxplot_panel(self, ax: plt.Axes, config: Dict) -> None:
        """ボックスプロットパネルを作成"""
        data = config.get("data", [])
        labels = config.get("labels", [])

        ax.boxplot(data, labels=labels)

        ax.set_xlabel(config.get("xlabel", ""))
        ax.set_ylabel(config.get("ylabel", ""))
        ax.set_title(config.get("title", ""))

    def save_figure(self, fig: plt.Figure, output_path: Path) -> None:
        """
        図を保存

        Args:
            fig: matplotlib Figure
            output_path: 保存パス
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig.savefig(output_path, dpi=self.config.dpi, bbox_inches="tight")

        plt.close(fig)

        self.logger.info(f"図を保存: {output_path}")

    def create_summary_statistics_plot(
        self,
        df: pd.DataFrame,
        group_column: str,
        value_columns: List[str],
        group1_value: str,
        group2_value: str,
    ) -> plt.Figure:
        """
        要約統計の可視化を作成

        Args:
            df: データフレーム
            group_column: グループを表すカラム名
            value_columns: 可視化する値のカラム名のリスト
            group1_value: 第1群の値
            group2_value: 第2群の値

        Returns:
            matplotlib Figure
        """
        plots_config = []

        for column in value_columns[:6]:  # 最大6パネル
            if column in df.columns:
                group1_data = df[df[group_column] == group1_value][column]
                group2_data = df[df[group_column] == group2_value][column]

                plots_config.append(
                    {
                        "type": "hist",
                        "data": [group1_data, group2_data],
                        "labels": [group1_value, group2_value],
                        "title": f"{column} Distribution",
                        "xlabel": column,
                        "ylabel": "Frequency",
                    }
                )

        return self.create_multi_panel_plot(
            plots_config, f"Distribution Comparison: {group1_value} vs {group2_value}"
        )
