"""TcEx Framework Module"""

from pydantic import field_serializer
from pydantic_settings import BaseSettings, SettingsConfigDict

from tcex_cli.input.field_type.sensitive import Sensitive


class ServiceModel(BaseSettings):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    # service model
    tc_svc_broker_cacert_file: str | None = None
    tc_svc_broker_cert_file: str | None = None
    tc_svc_broker_conn_timeout: int = 60
    tc_svc_broker_host: str = 'localhost'
    tc_svc_broker_port: int = 1883
    tc_svc_broker_timeout: int = 60
    tc_svc_broker_token: Sensitive | None = None
    tc_svc_client_topic: str = 'tcex-app-testing-client-topic'
    tc_svc_hb_timeout_seconds: int = 3600
    tc_svc_id: int | None = None
    tc_svc_server_topic: str = 'tcex-app-testing-server-topic'

    @field_serializer('tc_svc_broker_token')
    def serialize_sensitive_fields(self, value: Sensitive | None) -> str | None:
        """Serialize sensitive fields."""
        if value is not None and hasattr(value, 'value'):
            return value.value
        return value
