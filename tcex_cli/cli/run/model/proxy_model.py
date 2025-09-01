"""TcEx Framework Module"""

from pydantic import field_serializer
from pydantic_settings import BaseSettings, SettingsConfigDict

from tcex_cli.input.field_type.sensitive import Sensitive


class ProxyModel(BaseSettings):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    # proxy model
    tc_proxy_host: str | None = None
    tc_proxy_port: int | None = None
    tc_proxy_username: str | None = None
    tc_proxy_password: Sensitive | None = None
    tc_proxy_external: bool = False
    tc_proxy_tc: bool = False

    @field_serializer('tc_proxy_password')
    @classmethod
    def serialize_sensitive_fields(cls, value: Sensitive | None) -> str | None:
        """Serialize sensitive fields."""
        if value is not None and hasattr(value, 'value'):
            return value.value
        return value
