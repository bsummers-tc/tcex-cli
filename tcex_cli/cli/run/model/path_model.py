"""TcEx Framework Module"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class PathModel(BaseSettings):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    tc_in_path: Path = Path('log')
    tc_log_path: Path = Path('log')
    tc_out_path: Path = Path('log')
    tc_temp_path: Path = Path('log')
