#!/usr/bin/env python3
"""
Enricher Exceptions

エンリッチャー専用の例外クラスを定義する。
"""

from pathlib import Path
from typing import Optional


class EnricherError(Exception):
    """エンリッチャーのベース例外クラス"""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class MethodTracingError(EnricherError):
    """メソッド追跡に関するエラー"""

    def __init__(
        self,
        message: str,
        file_path: Optional[Path] = None,
        details: Optional[str] = None,
    ):
        super().__init__(message, details)
        self.file_path = file_path


class ClassificationError(EnricherError):
    """分類処理に関するエラー"""

    def __init__(
        self,
        message: str,
        method_a: Optional[str] = None,
        method_b: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(message, details)
        self.method_a = method_a
        self.method_b = method_b


class StatisticsError(EnricherError):
    """統計処理に関するエラー"""

    def __init__(
        self,
        message: str,
        pair_type: Optional[str] = None,
        category: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(message, details)
        self.pair_type = pair_type
        self.category = category


class TransitionProcessingError(EnricherError):
    """遷移処理に関するエラー"""

    def __init__(
        self,
        message: str,
        transition_dir: Optional[Path] = None,
        details: Optional[str] = None,
    ):
        super().__init__(message, details)
        self.transition_dir = transition_dir


class ConfigurationError(EnricherError):
    """設定に関するエラー"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(message, details)
        self.config_key = config_key
