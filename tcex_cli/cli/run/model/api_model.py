"""TcEx Framework Module"""

from pydantic import Field, field_serializer
from pydantic_settings import BaseSettings, SettingsConfigDict

from tcex_cli.input.field_type.sensitive import Sensitive


class ApiModel(BaseSettings):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    # api model
    api_default_org: str | None = None
    tc_api_access_id: str | None = None
    tc_api_path: str
    tc_api_secret_key: Sensitive | None = Field(None, description='A ThreatConnect API secret key.')
    tc_log_curl: bool = True
    tc_token: Sensitive | None = Field(None, description='A ThreatConnect API token.')
    tc_token_expires: int = 9999999999
    tc_verify: bool = False

    @field_serializer('tc_api_secret_key', 'tc_token')
    def convert_sensitive_to_value(self, value: Sensitive | None):
        """."""
        if value is not None and hasattr(value, 'value'):
            return value.value
        return value

    # @field_validator('tc_token', mode='before')
    # @classmethod
    # def one_set_of_credentials(cls, v: str, info: ValidationInfo):
    #     """Validate that one set of credentials is provided for the TC API."""
    #     _ij = InstallJson()

    #     # external Apps: require credentials and would not have an install.json file
    #     # organization (job) Apps: require credentials
    #     # playbook Apps: require credentials
    #     # service Apps: get token on createConfig message or during request
    #     if (
    #         _ij.fqfn.is_file() is False
    #         or (_ij.model.is_playbook_app or _ij.model.is_organization_app)
    #     ) and (
    #         v is None
    #         and not all([info.data.get('tc_api_access_id'), info.data.get('tc_api_secret_key')])
    #     ):
    #         ex_msg = (
    #             'At least one set of ThreatConnect credentials must be provided '
    #             '(tc_api_access_id/tc_api_secret key OR tc_token/tc_token_expires).'
    #         )
    #         raise ValueError(ex_msg)
    #     return v
