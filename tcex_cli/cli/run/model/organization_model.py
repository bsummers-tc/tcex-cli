"""TcEx Framework Module"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class OrganizationModel(BaseSettings):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    tc_job_id: int | None = None
