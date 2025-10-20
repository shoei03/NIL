#!/usr/bin/env python3
"""
ペアエンリッチメントツール

method_tracing.csvの情報を活用して、クローンペアの変化に詳細な分類と分析情報を付加する。
"""

import argparse
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd


class PairEnricher:
    """クローンペアにエンリッチメント情報を付加するクラス"""

    def __init__(self, output_dir: Path, similarity_threshold: float = 0.75):
        """
        Args:
            output_dir: 出力ディレクトリ（遷移ディレクトリの親）
            similarity_threshold: high_risk判定の類似度閾値
        """
        self.output_dir = output_dir
        self.similarity_threshold = similarity_threshold
        self.method_info: Dict[str, Dict[str, any]] = {}
        self.statistics = {
            'added': defaultdict(int),
            'deleted': defaultdict(int),
            'persisted': defaultdict(int)
        }

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
            logging.error(f"  method_tracing.csv not found: {method_tracing_path}")
            return
        except Exception as e:
            logging.error(f"  Error reading method_tracing.csv: {e}")
            return

        # 必須カラムのチェック
        required_columns = ['change_type', 'method_t_token_hash', 'method_t1_token_hash', 'similarity']
        if not all(col in df.columns for col in required_columns):
            logging.error(f"  method_tracing.csv is missing required columns: {required_columns}")
            return

        # トークンハッシュをキーとした辞書を構築
        # method_t_token_hash（前スナップショット）用
        for _, row in df.iterrows():
            change_type = row['change_type']
            method_t_hash = row['method_t_token_hash']
            method_t1_hash = row['method_t1_token_hash']
            similarity = row['similarity']

            # NaNを適切に処理
            if pd.notna(method_t_hash):
                method_t_hash = str(method_t_hash)
                if method_t_hash not in self.method_info:
                    self.method_info[method_t_hash] = {
                        'change_type': change_type,
                        'similarity': similarity if pd.notna(similarity) else None
                    }

            # method_t1_token_hash（後スナップショット）用
            if pd.notna(method_t1_hash):
                method_t1_hash = str(method_t1_hash)
                if method_t1_hash not in self.method_info:
                    self.method_info[method_t1_hash] = {
                        'change_type': change_type,
                        'similarity': similarity if pd.notna(similarity) else None
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
            return info['change_type'], info['similarity']
        else:
            logging.warning(f"Method {token_hash} not found in method_tracing.csv")
            return 'unknown', None

    def classify_deleted_pair(self, change_a: str, change_b: str) -> str:
        """deleted.csvのペアを分類"""
        if change_a == 'deleted' and change_b == 'deleted':
            return 'both_deleted'
        elif change_a == 'deleted':
            return 'method_a_deleted'
        elif change_b == 'deleted':
            return 'method_b_deleted'
        elif change_a in ['renamed', 'moved', 'signature_changed', 'refactored'] or \
             change_b in ['renamed', 'moved', 'signature_changed', 'refactored']:
            return 'pair_dissolved_by_refactoring'
        else:
            return 'pair_dissolved_naturally'

    def classify_added_pair(self, change_a: str, change_b: str) -> str:
        """added.csvのペアを分類"""
        if change_a == 'added' and change_b == 'added':
            return 'both_added'
        elif change_a == 'added':
            return 'method_a_added'
        elif change_b == 'added':
            return 'method_b_added'
        elif change_a in ['renamed', 'moved', 'signature_changed', 'refactored'] or \
             change_b in ['renamed', 'moved', 'signature_changed', 'refactored']:
            # さらに細分化: コピーの可能性
            if (change_a in ['exact', 'token_hash'] and change_b == 'refactored') or \
               (change_b in ['exact', 'token_hash'] and change_a == 'refactored'):
                return 'pair_formed_by_copy'
            else:
                return 'pair_formed_by_refactoring'
        else:
            return 'pair_formed_naturally'

    def classify_persisted_pair(self, change_a: str, change_b: str, 
                                similarity_a: Optional[float], similarity_b: Optional[float]) -> str:
        """persisted.csvのペアを分類"""
        if change_a in ['exact', 'token_hash'] and change_b in ['exact', 'token_hash']:
            return 'stable_unchanged'
        elif change_a == 'refactored' and change_b == 'refactored':
            # 類似度による細分化
            if (similarity_a is not None and similarity_a < self.similarity_threshold) or \
               (similarity_b is not None and similarity_b < self.similarity_threshold):
                return 'stable_both_refactored_high_risk'
            else:
                return 'stable_both_refactored'
        elif change_a == 'refactored' or change_b == 'refactored':
            # 類似度による細分化
            refactored_similarity = similarity_a if change_a == 'refactored' else similarity_b
            if refactored_similarity is not None and refactored_similarity < self.similarity_threshold:
                return 'stable_with_refactoring_high_risk'
            else:
                return 'stable_with_refactoring'
        else:
            return 'stable_with_minor_changes'

    def enrich_pairs(self, input_path: Path, output_path: Path, pair_type: str) -> None:
        """
        ペアCSVをエンリッチして出力
        
        Args:
            input_path: 入力CSVパス (added.csv, deleted.csv, persisted.csv)
            output_path: 出力CSVパス (*_enriched.csv)
            pair_type: 'added', 'deleted', 'persisted'のいずれか
        """
        try:
            df = pd.read_csv(input_path)
        except FileNotFoundError:
            logging.warning(f"File not found, skipping: {input_path}")
            return
        except Exception as e:
            logging.error(f"Error reading {input_path}: {e}")
            return

        # 空のファイルの場合
        if df.empty:
            logging.info(f"  {input_path.name}: empty file")
            # ヘッダーのみの出力ファイルを生成
            enriched_df = pd.DataFrame(columns=[
                'method_a', 'method_b', 'change_category',
                'method_a_change_type', 'method_b_change_type',
                'method_a_similarity', 'method_b_similarity'
            ])
            enriched_df.to_csv(output_path, index=False)
            return

        # 必須カラムのチェック
        if 'method_a' not in df.columns or 'method_b' not in df.columns:
            logging.error(f"{input_path.name} is missing required columns: method_a, method_b")
            return

        # エンリッチメント情報を追加
        enriched_rows = []
        for _, row in df.iterrows():
            method_a = str(row['method_a'])
            method_b = str(row['method_b'])

            # 各メソッドの変更情報を取得
            change_a, similarity_a = self.get_method_info(method_a)
            change_b, similarity_b = self.get_method_info(method_b)

            # カテゴリを分類
            if pair_type == 'deleted':
                category = self.classify_deleted_pair(change_a, change_b)
            elif pair_type == 'added':
                category = self.classify_added_pair(change_a, change_b)
            elif pair_type == 'persisted':
                category = self.classify_persisted_pair(change_a, change_b, similarity_a, similarity_b)
            else:
                category = 'unknown'

            # 統計情報を更新
            self.statistics[pair_type][category] += 1

            enriched_rows.append({
                'method_a': method_a,
                'method_b': method_b,
                'change_category': category,
                'method_a_change_type': change_a,
                'method_b_change_type': change_b,
                'method_a_similarity': similarity_a if similarity_a is not None else '',
                'method_b_similarity': similarity_b if similarity_b is not None else ''
            })

        # 出力
        enriched_df = pd.DataFrame(enriched_rows)
        enriched_df.to_csv(output_path, index=False)
        logging.info(f"  {input_path.name}: {len(enriched_rows)} pairs -> {output_path.name}")

    def process_transition_directory(self, transition_dir: Path) -> None:
        """遷移ディレクトリを処理"""
        logging.info(f"Processing transition: {transition_dir.name}")

        # この遷移ディレクトリ内のmethod_tracing.csvを読み込み
        method_tracing_path = transition_dir / 'method_tracing.csv'
        if not method_tracing_path.exists():
            logging.warning(f"  method_tracing.csv not found in {transition_dir.name}, skipping")
            return
        
        self.load_method_tracing(method_tracing_path)
        
        # method_tracing.csvが正しく読み込めなかった場合はスキップ
        if not self.method_info:
            logging.warning(f"  Failed to load method_tracing.csv, skipping transition")
            return

        # added.csv -> added_enriched.csv
        added_path = transition_dir / 'added.csv'
        added_enriched_path = transition_dir / 'added_enriched.csv'
        self.enrich_pairs(added_path, added_enriched_path, 'added')

        # deleted.csv -> deleted_enriched.csv
        deleted_path = transition_dir / 'deleted.csv'
        deleted_enriched_path = transition_dir / 'deleted_enriched.csv'
        self.enrich_pairs(deleted_path, deleted_enriched_path, 'deleted')

        # persisted.csv -> persisted_enriched.csv
        persisted_path = transition_dir / 'persisted.csv'
        persisted_enriched_path = transition_dir / 'persisted_enriched.csv'
        self.enrich_pairs(persisted_path, persisted_enriched_path, 'persisted')

    def find_transition_directories(self) -> list[Path]:
        """遷移ディレクトリを検索"""
        # ディレクトリ名パターン: YYYYMMDD_HHMMSS_hash_to_YYYYMMDD_HHMMSS_hash
        transition_dirs = []
        for item in self.output_dir.iterdir():
            if item.is_dir() and '_to_' in item.name:
                transition_dirs.append(item)
        return sorted(transition_dirs)

    def run(self) -> None:
        """メイン処理を実行"""
        logging.info("Starting pair enrichment")

        # 遷移ディレクトリを走査
        transition_dirs = self.find_transition_directories()
        if not transition_dirs:
            logging.warning(f"No transition directories found in {self.output_dir}")
            return

        logging.info(f"Found {len(transition_dirs)} transition directories")

        # 各遷移ディレクトリを処理
        for transition_dir in transition_dirs:
            self.process_transition_directory(transition_dir)

        # 統計情報を出力
        logging.info(f"Completed: {len(transition_dirs)} transitions processed")
        logging.info("Statistics:")
        for pair_type, categories in self.statistics.items():
            if categories:
                stats_str = ', '.join([f"{cat}={count}" for cat, count in sorted(categories.items())])
                logging.info(f"  {pair_type}: {stats_str}")


def setup_logging(log_file: Optional[Path] = None) -> None:
    """ログ設定"""
    log_format = '%(asctime)s %(levelname)s - %(message)s'
    log_level = logging.INFO

    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )


def main():
    parser = argparse.ArgumentParser(
        description='クローンペアにエンリッチメント情報を付加する'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        required=True,
        help='出力ディレクトリ（遷移ディレクトリの親）'
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        help='ログファイルのパス'
    )
    parser.add_argument(
        '--similarity-threshold',
        type=float,
        default=0.75,
        help='high_risk判定の類似度閾値（デフォルト: 0.75）'
    )

    args = parser.parse_args()

    # ログファイルのデフォルト設定
    if args.log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.log_file = Path('logs') / f'pair_enricher_{timestamp}.log'

    # ログ設定
    setup_logging(args.log_file)

    # エンリッチャーを実行
    enricher = PairEnricher(
        output_dir=args.output_dir,
        similarity_threshold=args.similarity_threshold
    )
    
    try:
        enricher.run()
        logging.info("Pair enrichment completed successfully")
    except Exception as e:
        logging.error(f"Pair enrichment failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()