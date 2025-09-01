"""TcEx Framework Module"""

from pydantic_settings import SettingsConfigDict

from tcex_cli.cli.run.model.common_app_input_model import CommonAppInputModel
from tcex_cli.cli.run.model.common_model import CommonModel
from tcex_cli.cli.run.model.playbook_common_model import PlaybookCommonModel
from tcex_cli.cli.run.model.service_model import ServiceModel


class AppTriggerServiceModel(CommonModel, PlaybookCommonModel, ServiceModel):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )


class AppTriggerInputModel(CommonAppInputModel):
    """Model Definition"""

    inputs: AppTriggerServiceModel
