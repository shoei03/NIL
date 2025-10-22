#!/usr/bin/env python3
"""
ログ設定ユーティリティ

共通のログ設定機能を提供する。
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_file: Optional[Path] = None) -> None:
    """
    ログ設定を行う

    Args:
        log_file: ログファイルのパス（Noneの場合は標準出力のみ）
    """
    log_format = "%(asctime)s %(levelname)s - %(message)s"
    log_level = logging.INFO

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)
