"""TcEx Framework Module"""

from pydantic_settings import SettingsConfigDict

from tcex_cli.cli.run.model.common_app_input_model import CommonAppInputModel
from tcex_cli.cli.run.model.common_model import CommonModel
from tcex_cli.cli.run.model.organization_model import OrganizationModel


class AppOrganizationModel(CommonModel, OrganizationModel):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )


class AppOrganizationInputModel(CommonAppInputModel):
    """Model Definition"""

    inputs: AppOrganizationModel
