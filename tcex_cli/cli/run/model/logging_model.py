"""TcEx Framework Module"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingModel(BaseSettings):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    # logging model
    tc_log_backup_count: int = 25
    tc_log_file: str = 'app.log'
    tc_log_level: str = 'trace'
    tc_log_max_bytes: int = 10_485_760
    tc_log_to_api: bool = False
