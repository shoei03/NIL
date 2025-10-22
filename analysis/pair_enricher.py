#!/usr/bin/env python3
"""
ペアエンリッチメントツール

method_tracing.csvの情報を活用して、クローンペアの変化に詳細な分類と分析情報を付加する。
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from enricher import PairEnricher
from utils import setup_logging


def main():
    parser = argparse.ArgumentParser(
        description="クローンペアにエンリッチメント情報を付加する"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="出力ディレクトリ（遷移ディレクトリの親）",
    )
    parser.add_argument("--log-file", type=Path, help="ログファイルのパス")
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.75,
        help="high_risk判定の類似度閾値（デフォルト: 0.75）",
    )

    args = parser.parse_args()

    # ログファイルのデフォルト設定
    if args.log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.log_file = Path("logs") / f"pair_enricher_{timestamp}.log"

    # ログ設定
    setup_logging(args.log_file)

    # エンリッチャーを実行
    enricher = PairEnricher(
        output_dir=args.output_dir, similarity_threshold=args.similarity_threshold
    )

    try:
        enricher.run()
        logging.info("Pair enrichment completed successfully")
    except Exception as e:
        logging.error(f"Pair enrichment failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
