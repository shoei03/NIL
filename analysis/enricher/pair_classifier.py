#!/usr/bin/env python3
"""
Pair Classifier

クローンペアの分類ロジックを提供するクラス。
"""

from typing import Optional

from .interfaces import PairClassifierInterface


class PairClassifier(PairClassifierInterface):
    """クローンペアの分類を行うクラス"""

    def __init__(self, similarity_threshold: float = 0.75):
        """
        初期化

        Args:
            similarity_threshold: high_risk判定の類似度閾値
        """
        self.similarity_threshold = similarity_threshold

    def classify_deleted_pair(self, change_a: str, change_b: str) -> str:
        """
        deleted.csvのペアを分類

        Args:
            change_a: メソッドAの変更タイプ
            change_b: メソッドBの変更タイプ

        Returns:
            分類カテゴリ
        """
        if change_a == "deleted" and change_b == "deleted":
            return "both_deleted"
        elif change_a == "deleted":
            return "method_a_deleted"
        elif change_b == "deleted":
            return "method_b_deleted"
        elif change_a in [
            "renamed",
            "moved",
            "signature_changed",
            "refactored",
        ] or change_b in ["renamed", "moved", "signature_changed", "refactored"]:
            return "pair_dissolved_by_refactoring"
        else:
            return "pair_dissolved_naturally"

    def classify_added_pair(self, change_a: str, change_b: str) -> str:
        """
        added.csvのペアを分類

        Args:
            change_a: メソッドAの変更タイプ
            change_b: メソッドBの変更タイプ

        Returns:
            分類カテゴリ
        """
        if change_a == "added" and change_b == "added":
            return "both_added"
        elif change_a == "added":
            return "method_a_added"
        elif change_b == "added":
            return "method_b_added"
        elif change_a in [
            "renamed",
            "moved",
            "signature_changed",
            "refactored",
        ] or change_b in ["renamed", "moved", "signature_changed", "refactored"]:
            # さらに細分化: コピーの可能性
            if (change_a in ["exact", "token_hash"] and change_b == "refactored") or (
                change_b in ["exact", "token_hash"] and change_a == "refactored"
            ):
                return "pair_formed_by_copy"
            else:
                return "pair_formed_by_refactoring"
        else:
            return "pair_formed_naturally"

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
        if change_a in ["exact", "token_hash"] and change_b in ["exact", "token_hash"]:
            return "stable_unchanged"
        elif change_a == "refactored" and change_b == "refactored":
            # 類似度による細分化
            if (
                similarity_a is not None and similarity_a < self.similarity_threshold
            ) or (
                similarity_b is not None and similarity_b < self.similarity_threshold
            ):
                return "stable_both_refactored_high_risk"
            else:
                return "stable_both_refactored"
        elif change_a == "refactored" or change_b == "refactored":
            # 類似度による細分化
            refactored_similarity = (
                similarity_a if change_a == "refactored" else similarity_b
            )
            if (
                refactored_similarity is not None
                and refactored_similarity < self.similarity_threshold
            ):
                return "stable_with_refactoring_high_risk"
            else:
                return "stable_with_refactoring"
        else:
            return "stable_with_minor_changes"
