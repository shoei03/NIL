"""
エンリッチャーモジュール

クローンペアのエンリッチメント処理に関するクラスとユーティリティを提供する。
"""

from .config import ConfigManager, EnricherConfig
from .exceptions import (
    ClassificationError,
    ConfigurationError,
    EnricherError,
    MethodTracingError,
    StatisticsError,
    TransitionProcessingError,
)
from .interfaces import (
    ConfigInterface,
    MethodTracingLoaderInterface,
    PairClassifierInterface,
    PairEnricherInterface,
    StatisticsCollectorInterface,
    TransitionProcessorInterface,
)
from .method_tracing_loader import MethodTracingLoader
from .pair_classifier import PairClassifier
from .pair_enricher import PairEnricher
from .statistics_collector import StatisticsCollector
from .transition_processor import TransitionProcessor

__all__ = [
    # 設定関連
    "EnricherConfig",
    "ConfigManager",
    # 例外
    "EnricherError",
    "MethodTracingError",
    "ClassificationError",
    "StatisticsError",
    "TransitionProcessingError",
    "ConfigurationError",
    # インターフェース
    "MethodTracingLoaderInterface",
    "PairClassifierInterface",
    "StatisticsCollectorInterface",
    "TransitionProcessorInterface",
    "PairEnricherInterface",
    "ConfigInterface",
    # 実装クラス
    "MethodTracingLoader",
    "PairClassifier",
    "PairEnricher",
    "StatisticsCollector",
    "TransitionProcessor",
]
