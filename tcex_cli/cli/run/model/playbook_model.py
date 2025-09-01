"""TcEx Framework Module"""

from uuid import uuid4

from pydantic_settings import BaseSettings, SettingsConfigDict

from tcex_cli.app.config.install_json import InstallJson


class PlaybookModel(BaseSettings):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    tc_kvstore_host: str = 'localhost'
    tc_kvstore_port: int = 6379
    tc_kvstore_type: str = 'Mock'
    tc_playbook_kvstore_context: str = str(uuid4())
    tc_playbook_out_variables: list[str] = InstallJson().tc_playbook_out_variables
