"""TcEx Framework Module"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BatchModel(BaseSettings):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    batch_action: str = 'Create'
    batch_chunk: int = 25_000
    batch_halt_on_error: bool = False
    batch_poll_interval: int = 15
    batch_poll_interval_max: int = 3_600
    batch_write_type: str = 'Append'
