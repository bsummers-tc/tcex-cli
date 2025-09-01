"""TcEx Framework Module"""

from pydantic_settings import SettingsConfigDict

from tcex_cli.cli.run.model.common_app_input_model import CommonAppInputModel
from tcex_cli.cli.run.model.common_model import CommonModel
from tcex_cli.cli.run.model.playbook_common_model import PlaybookCommonModel
from tcex_cli.cli.run.model.service_model import ServiceModel


class AppApiServiceModel(CommonModel, PlaybookCommonModel, ServiceModel):
    """Model Definition

    The inputs defined below should all be read from environment
    variables. Either defined globally or in the local .env file.
    Default values are provided when possible.
    """

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    # HTTP Server model
    api_service_host: str = 'localhost'
    api_service_port: int = 8042

    @property
    def server_url(self) -> str:
        """Return the server url."""
        return f'http://{self.api_service_host}:{self.api_service_port}'


class AppApiInputModel(CommonAppInputModel):
    """Model Definition"""

    inputs: AppApiServiceModel
