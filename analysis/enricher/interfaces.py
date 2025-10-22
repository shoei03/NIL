#!/usr/bin/env python3
"""
Enricher Interfaces

エンリッチャーのインターフェースを定義する。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class MethodTracingLoaderInterface(ABC):
    """メソッド追跡ローダーのインターフェース"""

    @abstractmethod
    def load_method_tracing(self, method_tracing_path: Path) -> None:
        """
        method_tracing.csvを読み込み、辞書を構築

        Args:
            method_tracing_path: method_tracing.csvのパス
        """
        pass

    @abstractmethod
    def get_method_info(self, token_hash: str) -> Tuple[str, Optional[float]]:
        """
        トークンハッシュから変更情報を取得

        Args:
            token_hash: メソッドのトークンハッシュ

        Returns:
            (change_type, similarity) のタプル
        """
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """
        メソッド情報が読み込まれているかチェック

        Returns:
            読み込まれている場合はTrue
        """
        pass


class PairClassifierInterface(ABC):
    """ペア分類器のインターフェース"""

    @abstractmethod
    def classify_deleted_pair(self, change_a: str, change_b: str) -> str:
        """
        deleted.csvのペアを分類

        Args:
            change_a: メソッドAの変更タイプ
            change_b: メソッドBの変更タイプ

        Returns:
            分類カテゴリ
        """
        pass

    @abstractmethod
    def classify_added_pair(self, change_a: str, change_b: str) -> str:
        """
        added.csvのペアを分類

        Args:
            change_a: メソッドAの変更タイプ
            change_b: メソッドBの変更タイプ

        Returns:
            分類カテゴリ
        """
        pass

    @abstractmethod
    def classify_persisted_pair(
        self,
        change_a: str,
        change_b: str,
        similarity_a: Optional[float],
        similarity_b: Optional[float],
    ) -> str:
        """
        persisted.csvのペアを分類

        Args:
            change_a: メソッドAの変更タイプ
            change_b: メソッドBの変更タイプ
            similarity_a: メソッドAの類似度
            similarity_b: メソッドBの類似度

        Returns:
            分類カテゴリ
        """
        pass


class StatisticsCollectorInterface(ABC):
    """統計収集器のインターフェース"""

    @abstractmethod
    def add_statistic(self, pair_type: str, category: str) -> None:
        """
        統計情報を追加

        Args:
            pair_type: ペアタイプ ('added', 'deleted', 'persisted')
            category: 分類カテゴリ
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        統計情報を取得

        Returns:
            統計情報の辞書
        """
        pass

    @abstractmethod
    def log_statistics(self) -> None:
        """統計情報をログに出力"""
        pass

    @abstractmethod
    def reset(self) -> None:
        """統計情報をリセット"""
        pass


class TransitionProcessorInterface(ABC):
    """遷移プロセッサーのインターフェース"""

    @abstractmethod
    def process_transition_directory(self, transition_dir: Path) -> None:
        """
        遷移ディレクトリを処理

        Args:
            transition_dir: 遷移ディレクトリのパス
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        統計情報を取得

        Returns:
            統計情報の辞書
        """
        pass

    @abstractmethod
    def log_statistics(self) -> None:
        """統計情報をログに出力"""
        pass


class PairEnricherInterface(ABC):
    """ペアエンリッチャーのインターフェース"""

    @abstractmethod
    def run(self) -> None:
        """メイン処理を実行"""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        統計情報を取得

        Returns:
            統計情報の辞書
        """
        pass


class ConfigInterface(ABC):
    """設定管理のインターフェース"""

    @abstractmethod
    def load_config(self, **kwargs) -> Any:
        """
        設定を読み込み

        Args:
            **kwargs: 設定のオーバーライド値

        Returns:
            設定オブジェクト
        """
        pass

    @abstractmethod
    def save_config(self, config: Any, output_path: Optional[Path] = None) -> None:
        """
        設定を保存

        Args:
            config: 保存する設定
            output_path: 出力パス
        """
        pass
