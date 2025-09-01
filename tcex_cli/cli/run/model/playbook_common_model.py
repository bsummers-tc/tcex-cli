"""TcEx Framework Module"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class PlaybookCommonModel(BaseSettings):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    tc_cache_kvstore_id: int = 10
    tc_kvstore_host: str = 'localhost'
    tc_kvstore_port: int = 6379
    tc_kvstore_type: str = 'Redis'
    tc_playbook_kvstore_id: int = 0
