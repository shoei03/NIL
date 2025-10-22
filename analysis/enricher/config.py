#!/usr/bin/env python3
"""
Enricher Configuration

エンリッチャーの設定管理を行うクラス。
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import ConfigurationError


@dataclass
class EnricherConfig:
    """エンリッチャーの設定クラス"""

    # 基本設定
    output_dir: Path
    similarity_threshold: float = 0.75
    log_level: str = "INFO"

    # ログ設定
    log_file: Optional[Path] = None
    log_to_console: bool = True
    log_to_file: bool = True

    # 処理設定
    max_workers: Optional[int] = None
    cache_size: int = 1000
    batch_size: int = 1000

    # 分類設定
    high_risk_threshold: float = 0.75
    enable_parallel_processing: bool = True

    def __post_init__(self):
        """設定値の検証"""
        if not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)

        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ConfigurationError(
                f"similarity_threshold must be between 0.0 and 1.0, got {self.similarity_threshold}",
                config_key="similarity_threshold",
            )

        if not (0.0 <= self.high_risk_threshold <= 1.0):
            raise ConfigurationError(
                f"high_risk_threshold must be between 0.0 and 1.0, got {self.high_risk_threshold}",
                config_key="high_risk_threshold",
            )

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ConfigurationError(
                f"log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL, got {self.log_level}",
                config_key="log_level",
            )


class ConfigManager:
    """設定管理クラス"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        初期化

        Args:
            config_path: 設定ファイルのパス（Noneの場合はデフォルト設定）
        """
        self.config_path = config_path
        self._config: Optional[EnricherConfig] = None

    def load_config(self, **kwargs) -> EnricherConfig:
        """
        設定を読み込み

        Args:
            **kwargs: 設定のオーバーライド値

        Returns:
            設定オブジェクト
        """
        if self.config_path and self.config_path.exists():
            config_dict = self._load_from_file()
        else:
            config_dict = {}

        # キーワード引数でオーバーライド
        config_dict.update(kwargs)

        try:
            self._config = EnricherConfig(**config_dict)
            return self._config
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def _load_from_file(self) -> Dict[str, Any]:
        """設定ファイルから読み込み"""
        try:
            if self.config_path.suffix == ".json":
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                raise ConfigurationError(
                    f"Unsupported config file format: {self.config_path.suffix}"
                )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load config file {self.config_path}: {e}"
            ) from e

    def save_config(
        self, config: EnricherConfig, output_path: Optional[Path] = None
    ) -> None:
        """
        設定を保存

        Args:
            config: 保存する設定
            output_path: 出力パス（Noneの場合は初期化時のパス）
        """
        save_path = output_path or self.config_path
        if save_path is None:
            raise ConfigurationError("No output path specified for saving config")

        try:
            config_dict = asdict(config)
            # Pathオブジェクトを文字列に変換
            for key, value in config_dict.items():
                if isinstance(value, Path):
                    config_dict[key] = str(value)

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save config to {save_path}: {e}"
            ) from e

    def get_config(self) -> Optional[EnricherConfig]:
        """現在の設定を取得"""
        return self._config

    def create_default_config(self, output_dir: Path, **kwargs) -> EnricherConfig:
        """
        デフォルト設定を作成

        Args:
            output_dir: 出力ディレクトリ
            **kwargs: 追加の設定値

        Returns:
            デフォルト設定オブジェクト
        """
        default_config = {"output_dir": output_dir, **kwargs}

        try:
            return EnricherConfig(**default_config)
        except Exception as e:
            raise ConfigurationError(f"Failed to create default config: {e}") from e
