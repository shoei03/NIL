#!/usr/bin/env python3
"""
Method Tracing Loader

method_tracing.csvファイルの読み込みと管理を行うクラス。
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from .exceptions import MethodTracingError
from .interfaces import MethodTracingLoaderInterface


class MethodTracingLoader(MethodTracingLoaderInterface):
    """method_tracing.csvの読み込みと管理を行うクラス"""

    def __init__(self):
        """初期化"""
        self.method_info: Dict[str, Dict[str, any]] = {}

    def load_method_tracing(self, method_tracing_path: Path) -> None:
        """
        method_tracing.csvを読み込み、辞書を構築

        Args:
            method_tracing_path: method_tracing.csvのパス
        """
        logging.info(f"  Loading method_tracing.csv from {method_tracing_path}")

        # 辞書をクリア（各遷移ごとに独立して処理）
        self.method_info.clear()

        try:
            df = pd.read_csv(method_tracing_path)
        except FileNotFoundError:
            error_msg = f"method_tracing.csv not found: {method_tracing_path}"
            logging.error(f"  {error_msg}")
            raise MethodTracingError(error_msg, file_path=method_tracing_path)
        except Exception as e:
            error_msg = f"Error reading method_tracing.csv: {e}"
            logging.error(f"  {error_msg}")
            raise MethodTracingError(
                error_msg, file_path=method_tracing_path, details=str(e)
            )

        # 必須カラムのチェック
        required_columns = [
            "change_type",
            "method_t_token_hash",
            "method_t1_token_hash",
            "similarity",
        ]
        if not all(col in df.columns for col in required_columns):
            error_msg = (
                f"method_tracing.csv is missing required columns: {required_columns}"
            )
            logging.error(f"  {error_msg}")
            raise MethodTracingError(
                error_msg,
                file_path=method_tracing_path,
                details=f"Missing columns: {set(required_columns) - set(df.columns)}",
            )

        # トークンハッシュをキーとした辞書を構築
        # method_t_token_hash（前スナップショット）用
        for _, row in df.iterrows():
            change_type = row["change_type"]
            method_t_hash = row["method_t_token_hash"]
            method_t1_hash = row["method_t1_token_hash"]
            similarity = row["similarity"]

            # NaNを適切に処理
            if pd.notna(method_t_hash):
                method_t_hash = str(method_t_hash)
                if method_t_hash not in self.method_info:
                    self.method_info[method_t_hash] = {
                        "change_type": change_type,
                        "similarity": similarity if pd.notna(similarity) else None,
                    }

            # method_t1_token_hash（後スナップショット）用
            if pd.notna(method_t1_hash):
                method_t1_hash = str(method_t1_hash)
                if method_t1_hash not in self.method_info:
                    self.method_info[method_t1_hash] = {
                        "change_type": change_type,
                        "similarity": similarity if pd.notna(similarity) else None,
                    }

        logging.info(f"  Loaded {len(self.method_info)} unique method token hashes")

    def get_method_info(self, token_hash: str) -> Tuple[str, Optional[float]]:
        """
        トークンハッシュから変更情報を取得

        Args:
            token_hash: メソッドのトークンハッシュ

        Returns:
            (change_type, similarity) のタプル
        """
        if token_hash in self.method_info:
            info = self.method_info[token_hash]
            return info["change_type"], info["similarity"]
        else:
            logging.warning(f"Method {token_hash} not found in method_tracing.csv")
            return "unknown", None

    def is_loaded(self) -> bool:
        """
        メソッド情報が読み込まれているかチェック

        Returns:
            読み込まれている場合はTrue
        """
        return len(self.method_info) > 0
