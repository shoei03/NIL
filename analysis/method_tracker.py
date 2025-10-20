#!/usr/bin/env python3
"""
Method Evolution Tracker (rewritten with split output)

Features / improvements over previous version:
- Prevent duplicate logger handlers when creating multiple trackers in the same process
- Robust token_sequence parsing (ignore empty/non-integer tokens)
- Normalize similarity scores returned by SimilarityCalculator (support 0..1 and 0..100)
- CLI thresholds accepted as percentages or fractions but normalized internally
- Split output: each pair comparison saves to separate directory with method_tracing.csv
"""

import argparse
import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from similarity_calculator import SimilarityCalculator
from tqdm import tqdm


@dataclass(frozen=True)
class MethodInfo:
    file_path: str
    start_line: int
    end_line: int
    method_name: str
    return_type: str
    parameters: str
    commit_hash: str
    token_hash: str
    token_sequence: Optional[List[int]] = None

    @property
    def signature(self) -> str:
        return f"{self.method_name}:{self.parameters}:{self.return_type}"

    @property
    def full_id(self) -> str:
        return f"{self.file_path}::{self.signature}"

    def __str__(self) -> str:
        return f"{self.file_path}:{self.start_line}-{self.end_line}:{self.method_name}"


@dataclass
class MethodMatch:
    method_t: MethodInfo
    method_t1: MethodInfo
    match_type: str
    similarity: float = 1.0


class SimilarityWrapper:
    """Wrap SimilarityCalculator to normalize scores to 0..1."""

    def __init__(self, gram_size: int = 5):
        self.calc = SimilarityCalculator(gram_size=gram_size)

    @staticmethod
    def _normalize(value: Optional[float]) -> float:
        if value is None:
            return 0.0
        try:
            v = float(value)
        except Exception:
            return 0.0

        # If value looks like percentage (> 1.0), scale to 0..1
        if v > 1.0:
            v = v / 100.0

        # Clamp
        if v < 0.0:
            return 0.0
        if v > 1.0:
            return 1.0
        return v

    def calc_ngram_similarity(self, a: List[int], b: List[int]) -> float:
        raw = self.calc.calc_ngram_similarity(a, b)
        return self._normalize(raw)

    def calc_lcs_similarity(self, a: List[int], b: List[int]) -> float:
        raw = self.calc.calc_lcs_similarity(a, b)
        return self._normalize(raw)


class MethodTracker:
    def __init__(
        self,
        log_file: Optional[Path] = None,
        use_similarity: bool = False,
        ngram_threshold: float = 0.10,
        lcs_threshold: float = 0.70,
    ) -> None:
        """Initialize MethodTracker.

        ngram_threshold and lcs_threshold are expected as normalized floats (0..1).
        CLI accepts percentages (e.g. 10, 70) or fractions (0.1, 0.7).
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Create log file path if not provided
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"method_tracker_{timestamp}.log"

        # Prevent adding duplicate handlers if logger already configured
        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

        self.log_file = log_file

        # Similarity configuration
        self.use_similarity = use_similarity
        # thresholds are normalized in case caller passed percents
        self.ngram_threshold = self._normalize_threshold(ngram_threshold)
        self.lcs_threshold = self._normalize_threshold(lcs_threshold)

        self.similarity_calc = None
        if self.use_similarity:
            self.similarity_calc = SimilarityWrapper(gram_size=5)
            self.logger.info(
                f"Similarity matching enabled: N-gram threshold={self.ngram_threshold:.3f}, LCS threshold={self.lcs_threshold:.3f}"
            )

    @staticmethod
    def _normalize_threshold(value: float) -> float:
        try:
            v = float(value)
        except Exception:
            return 0.0
        if v > 1.0:
            v = v / 100.0
        if v < 0.0:
            return 0.0
        if v > 1.0:
            return 1.0
        return v

    def parse_code_blocks(self, file_path: Path) -> Dict[str, MethodInfo]:
        methods: Dict[str, MethodInfo] = {}
        error_count = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for line_num, row in enumerate(reader, 1):
                    if not row:
                        continue

                    try:
                        if len(row) == 9:
                            token_hash_val = row[0].strip()
                            file_p = row[1].strip()
                            start = int(row[2])
                            end = int(row[3])
                            method = row[4].strip()
                            ret_type = row[5].strip()
                            params = row[6].strip()
                            commit_hash = row[7].strip()
                            token_seq_str = row[8]

                            token_sequence: Optional[List[int]] = None
                            if token_seq_str and token_seq_str.strip():
                                parts = [
                                    p.strip()
                                    for p in token_seq_str.split(";")
                                    if p and p.strip()
                                ]
                                seq: List[int] = []
                                for t in parts:
                                    try:
                                        seq.append(int(t))
                                    except Exception:
                                        # ignore non-integer tokens but log once at debug level
                                        self.logger.debug(
                                            f"{file_path.name}:{line_num}: invalid token in sequence: {t}"
                                        )
                                token_sequence = seq

                            method_info = MethodInfo(
                                file_path=file_p,
                                start_line=start,
                                end_line=end,
                                method_name=method,
                                return_type=ret_type,
                                parameters=params,
                                commit_hash=commit_hash,
                                token_hash=token_hash_val,
                                token_sequence=token_sequence,
                            )

                            methods[method_info.full_id] = method_info

                        elif len(row) == 3:
                            # legacy format: skip
                            continue
                        else:
                            error_count += 1
                            self.logger.warning(
                                f"{file_path.name}:{line_num}: Unexpected format ({len(row)} columns)"
                            )

                    except Exception as e:
                        error_count += 1
                        self.logger.warning(
                            f"{file_path.name}:{line_num}: Error parsing line - {str(e)}"
                        )

        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {str(e)}")
            raise

        if error_count > 0:
            self.logger.warning(
                f"{file_path.name}: Parsed with {error_count} errors, {len(methods)} methods extracted"
            )
        else:
            self.logger.info(f"{file_path.name}: {len(methods)} methods extracted")

        return methods

    def find_exact_matches(
        self,
        snapshot_t: Dict[str, MethodInfo],
        snapshot_t1: Dict[str, MethodInfo],
    ) -> List[MethodMatch]:
        matches: List[MethodMatch] = []
        for full_id, method_info in snapshot_t.items():
            if full_id in snapshot_t1:
                matches.append(
                    MethodMatch(
                        method_t=method_info,
                        method_t1=snapshot_t1[full_id],
                        match_type="exact",
                        similarity=1.0,
                    )
                )
        return matches

    def find_token_hash_matches(
        self,
        unmatched_t: Dict[str, MethodInfo],
        unmatched_t1: Dict[str, MethodInfo],
    ) -> List[MethodMatch]:
        matches: List[MethodMatch] = []

        hash_to_methods_t: Dict[str, List[MethodInfo]] = {}
        for method in unmatched_t.values():
            if method.token_hash:
                hash_to_methods_t.setdefault(method.token_hash, []).append(method)

        hash_to_methods_t1: Dict[str, List[MethodInfo]] = {}
        for method in unmatched_t1.values():
            if method.token_hash:
                hash_to_methods_t1.setdefault(method.token_hash, []).append(method)

        for token_hash, methods_t in hash_to_methods_t.items():
            if token_hash in hash_to_methods_t1:
                methods_t1 = hash_to_methods_t1[token_hash][:]
                for method_t in methods_t:
                    if not methods_t1:
                        break
                    method_t1 = methods_t1.pop(0)
                    matches.append(
                        MethodMatch(
                            method_t=method_t,
                            method_t1=method_t1,
                            match_type="token_hash",
                            similarity=1.0,
                        )
                    )

        return matches

    def find_similarity_matches(
        self,
        unmatched_t: Dict[str, MethodInfo],
        unmatched_t1: Dict[str, MethodInfo],
    ) -> List[MethodMatch]:
        if not self.use_similarity or self.similarity_calc is None:
            return []

        matches: List[MethodMatch] = []
        matched_t: Set[str] = set()
        matched_t1: Set[str] = set()

        methods_t = [
            (mid, m)
            for mid, m in unmatched_t.items()
            if m.token_sequence and len(m.token_sequence) > 0
        ]
        methods_t1 = [
            (mid, m)
            for mid, m in unmatched_t1.items()
            if m.token_sequence and len(m.token_sequence) > 0
        ]

        self.logger.info(
            f"Finding similarity matches: {len(methods_t)} x {len(methods_t1)} comparisons"
        )

        for method_id_t, method_t in methods_t:
            if method_id_t in matched_t:
                continue

            best_match = None
            best_lcs_sim = 0.0

            for method_id_t1, method_t1 in methods_t1:
                if method_id_t1 in matched_t1:
                    continue

                ngram_sim = self.similarity_calc.calc_ngram_similarity(
                    method_t.token_sequence, method_t1.token_sequence
                )

                if ngram_sim < self.ngram_threshold:
                    continue

                lcs_sim = self.similarity_calc.calc_lcs_similarity(
                    method_t.token_sequence, method_t1.token_sequence
                )

                if lcs_sim >= self.lcs_threshold and lcs_sim > best_lcs_sim:
                    best_lcs_sim = lcs_sim
                    best_match = (method_id_t1, method_t1, lcs_sim)

            if best_match:
                method_id_t1, method_t1, lcs_sim = best_match

                if method_t.file_path == method_t1.file_path:
                    if method_t.method_name == method_t1.method_name:
                        match_type = "signature_changed"
                    elif lcs_sim >= 0.90:
                        match_type = "renamed"
                    else:
                        match_type = "refactored"
                elif lcs_sim >= 0.90:
                    match_type = "moved"
                else:
                    match_type = "refactored"

                matches.append(
                    MethodMatch(
                        method_t=method_t,
                        method_t1=method_t1,
                        match_type=match_type,
                        similarity=lcs_sim,
                    )
                )

                matched_t.add(method_id_t)
                matched_t1.add(method_id_t1)

        self.logger.info(f"Found {len(matches)} similarity-based matches")
        return matches

    def analyze_changes(
        self,
        snapshot_t: Dict[str, MethodInfo],
        snapshot_t1: Dict[str, MethodInfo],
    ) -> Tuple[List[MethodMatch], Set[str], Set[str]]:
        all_matches: List[MethodMatch] = []

        exact_matches = self.find_exact_matches(snapshot_t, snapshot_t1)
        all_matches.extend(exact_matches)
        self.logger.info(f"Exact matches: {len(exact_matches)}")

        matched_t = {match.method_t.full_id for match in all_matches}
        matched_t1 = {match.method_t1.full_id for match in all_matches}

        unmatched_t = {k: v for k, v in snapshot_t.items() if k not in matched_t}
        unmatched_t1 = {k: v for k, v in snapshot_t1.items() if k not in matched_t1}

        if unmatched_t and unmatched_t1:
            token_matches = self.find_token_hash_matches(unmatched_t, unmatched_t1)
            all_matches.extend(token_matches)
            self.logger.info(f"Token hash matches: {len(token_matches)}")

            for match in token_matches:
                matched_t.add(match.method_t.full_id)
                matched_t1.add(match.method_t1.full_id)

            unmatched_t = {k: v for k, v in snapshot_t.items() if k not in matched_t}
            unmatched_t1 = {k: v for k, v in snapshot_t1.items() if k not in matched_t1}

        if self.use_similarity and unmatched_t and unmatched_t1:
            sim_matches = self.find_similarity_matches(unmatched_t, unmatched_t1)
            all_matches.extend(sim_matches)

            for match in sim_matches:
                matched_t.add(match.method_t.full_id)
                matched_t1.add(match.method_t1.full_id)

        added_ids = set(snapshot_t1.keys()) - matched_t1
        deleted_ids = set(snapshot_t.keys()) - matched_t

        return all_matches, added_ids, deleted_ids

    def track_methods(
        self,
        code_blocks_dir: Path,
        output_base_dir: Path,
        code_block_filename: str = "code_blocks.csv",
    ) -> None:
        """Track methods across snapshots and save each pair comparison to separate directory."""
        # スナップショットディレクトリの収集
        snapshot_dirs = sorted(
            d for d in code_blocks_dir.iterdir()
            if d.is_dir() and (d / code_block_filename).exists()
        )
        
        code_block_files = [d / code_block_filename for d in snapshot_dirs]
        
        if len(code_block_files) < 2:
            self.logger.warning(
                f"Need at least 2 code_blocks files to track methods (found {len(code_block_files)})"
            )
            return
        
        self.logger.info(f"Processing {len(code_block_files)} code_blocks files")
        
        # 出力ディレクトリを作成
        output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # 全体のサマリーファイルを準備
        summary_file = output_base_dir / "method_tracking_summary.csv"
        with open(summary_file, "w", newline="", encoding="utf-8") as summary_f:
            summary_writer = csv.writer(summary_f)
            
            # サマリーヘッダー
            summary_writer.writerow([
                "snapshot_t", "snapshot_t1", "exact_matches", "token_hash_matches",
                "renamed", "moved", "signature_changed", "refactored",
                "added_methods", "deleted_methods", "total_t", "total_t1"
            ])
            
            # スナップショット間の比較
            for prev_file, curr_file in tqdm(
                zip(code_block_files, code_block_files[1:]),
                total=len(code_block_files) - 1,
                desc="Tracking methods"
            ):
                prev_snapshot = self.parse_code_blocks(prev_file)
                curr_snapshot = self.parse_code_blocks(curr_file)
                
                # ディレクトリ名から情報を抽出
                prev_dir_name = prev_file.parent.name
                curr_dir_name = curr_file.parent.name
                
                # 出力ディレクトリ名を作成: YYYYMMDD_HHMMSS_commit_to_YYYYMMDD_HHMMSS_commit
                output_dir_name = f"{prev_dir_name}_to_{curr_dir_name}"
                output_dir = output_base_dir / output_dir_name
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # method_tracing.csvに書き込み + サマリー情報を取得
                match_counts, added_count, deleted_count = self._write_pair_comparison(
                    output_dir / "method_tracing.csv",
                    prev_snapshot,
                    curr_snapshot,
                    prev_dir_name,
                    curr_dir_name
                )
                
                # サマリー行を追加
                summary_writer.writerow([
                    prev_dir_name, curr_dir_name,
                    match_counts["exact"], match_counts["token_hash"],
                    match_counts["renamed"], match_counts["moved"],
                    match_counts["signature_changed"], match_counts["refactored"],
                    added_count, deleted_count,
                    len(prev_snapshot), len(curr_snapshot)
                ])
                
                self.logger.info(f"Written: {output_dir / 'method_tracing.csv'}")
        
        self.logger.info(f"Summary written to {summary_file}")
        self.logger.info("Method tracking complete!")

    def _write_pair_comparison(
        self,
        output_file: Path,
        prev_snapshot: Dict[str, MethodInfo],
        curr_snapshot: Dict[str, MethodInfo],
        prev_label: str,
        curr_label: str,
    ) -> Tuple[Dict[str, int], int, int]:
        """2つのスナップショット間の変更を分析してCSVに書き込む
        
        Returns:
            Tuple[Dict[str, int], int, int]: (match_counts, added_count, deleted_count)
        """
        matches, added_ids, deleted_ids = self.analyze_changes(prev_snapshot, curr_snapshot)
        
        # マッチタイプのカウント
        match_counts = {t: 0 for t in ["exact", "token_hash", "renamed", "moved", "signature_changed", "refactored"]}
        for match in matches:
            match_counts[match.match_type] += 1
        
        # CSVに書き込み
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # ヘッダー
            writer.writerow([
                "change_type",
                "method_t_token_hash",
                "method_t1_token_hash",
                "similarity"
            ])
            
            # マッチしたメソッド
            for match in matches:
                writer.writerow([
                    match.match_type,
                    match.method_t.token_hash,
                    match.method_t1.token_hash,
                    f"{match.similarity:.3f}"
                ])
            
            # 追加されたメソッド
            for method_id in added_ids:
                method = curr_snapshot[method_id]
                writer.writerow([
                    "added",
                    "",
                    method.token_hash,
                    ""
                ])
            
            # 削除されたメソッド
            for method_id in deleted_ids:
                method = prev_snapshot[method_id]
                writer.writerow([
                    "deleted",
                    method.token_hash,
                    "",
                    ""
                ])
        
        self.logger.info(
            f"{prev_label} -> {curr_label}: "
            f"exact={match_counts['exact']}, token_hash={match_counts['token_hash']}, "
            f"renamed={match_counts['renamed']}, moved={match_counts['moved']}, "
            f"sig_changed={match_counts['signature_changed']}, refactored={match_counts['refactored']}, "
            f"added={len(added_ids)}, deleted={len(deleted_ids)}"
        )
        
        return match_counts, len(added_ids), len(deleted_ids)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Track methods across code_blocks snapshots (Phase 1 & 2) with split output"
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=Path("/workspace/results/"),
        help="Directory containing snapshot subdirs with code_blocks.csv (default: /workspace/results/)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("/app/output/pair_diff_with_lists"),
        help="Base output directory (will create subdirs for each pair comparison) (default: /app/output/pair_diff_with_lists)",
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default="code_blocks.csv",
        help="Filename of code blocks CSV inside each snapshot dir (default: code_blocks.csv)",
    )
    parser.add_argument("--log", type=Path, help="Log file path (optional)")
    parser.add_argument(
        "--no-similarity",
        action="store_true",
        help="Disable Phase 2 similarity-based matching (similarity is enabled by default)",
    )
    parser.add_argument(
        "--ngram-threshold",
        type=float,
        default=10.0,
        help="N-gram similarity threshold (percent or fraction) (default: 10.0)",
    )
    parser.add_argument(
        "--lcs-threshold",
        type=float,
        default=70.0,
        help="LCS similarity threshold (percent or fraction) (default: 70.0)",
    )

    args = parser.parse_args()

    # Similarity is enabled by default, unless --no-similarity is specified
    use_similarity = not args.no_similarity

    # `MethodTracker` normalizes thresholds internally, so pass CLI values directly
    tracker = MethodTracker(
        log_file=args.log,
        use_similarity=use_similarity,
        ngram_threshold=args.ngram_threshold,
        lcs_threshold=args.lcs_threshold,
    )
    tracker.logger.info(f"Input directory: {args.input_dir}")
    tracker.logger.info(f"Output base directory: {args.output_dir}")
    tracker.logger.info(f"Log file: {tracker.log_file}")

    tracker.track_methods(
        args.input_dir,
        args.output_dir,
        code_block_filename=args.input_file,
    )


if __name__ == "__main__":
    main()