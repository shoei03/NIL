#!/usr/bin/env python3
"""
設定管理モジュール

分析に必要な全ての設定を統一管理する。
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AnalysisConfig:
    """分析設定の統一管理"""

    # 閾値設定
    ngram_threshold: int = 50
    lcs_threshold: int = 60
    high_similarity_threshold: int = 80
    medium_similarity_threshold: int = 60
    low_similarity_threshold: int = 40

    # パス設定
    results_dir: Path = Path("../results")
    output_dir: Path = Path("./output")

    # 分析設定
    enable_visualization: bool = True
    enable_statistical_tests: bool = True
    log_level: str = "INFO"

    # 可視化設定
    figure_size: tuple = (12, 8)
    dpi: int = 300
    alpha: float = 0.7
    bins: int = 20

    # 統計検定設定
    significance_level: float = 0.05
    enable_multiple_comparison_correction: bool = True
    enable_bonferroni_correction: bool = True
    alternative: str = "two-sided"

    def __post_init__(self):
        """設定の後処理"""
        # パスを絶対パスに変換
        self.results_dir = self.results_dir.resolve()
        self.output_dir = self.output_dir.resolve()

        # 出力ディレクトリを作成
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_log_file_path(self, analysis_type: str) -> Path:
        """ログファイルのパスを取得"""
        return self.output_dir / f"{analysis_type}_analysis.log"

    def get_output_subdir(self, analysis_type: str) -> Path:
        """分析タイプ別の出力ディレクトリを取得"""
        subdir = self.output_dir / analysis_type
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    def get_corrected_alpha(self, num_tests: int) -> float:
        """Bonferroni補正後の有意水準を取得"""
        if self.enable_bonferroni_correction:
            return self.significance_level / num_tests
        return self.significance_level


@dataclass
class SimilarityThresholds:
    """類似度閾値の定義"""

    HIGH: int = 80
    MEDIUM: int = 60
    LOW: int = 40
    VERY_LOW: int = 0

    def get_level(self, similarity: float) -> str:
        """類似度からレベルを取得"""
        if similarity >= self.HIGH:
            return "high"
        elif similarity >= self.MEDIUM:
            return "medium"
        elif similarity >= self.LOW:
            return "low"
        else:
            return "very_low"

    def get_level_thresholds(self) -> dict:
        """レベル別閾値を辞書で取得"""
        return {
            "high": self.HIGH,
            "medium": self.MEDIUM,
            "low": self.LOW,
            "very_low": self.VERY_LOW,
        }


@dataclass
class StatisticalTestConfig:
    """統計検定の設定"""

    significance_level: float = 0.05
    enable_bonferroni_correction: bool = True
    alternative: str = "two-sided"

    def get_corrected_alpha(self, num_tests: int) -> float:
        """Bonferroni補正後の有意水準を取得"""
        if self.enable_bonferroni_correction:
            return self.significance_level / num_tests
        return self.significance_level
