"""TcEx Framework Module"""

from pydantic_settings import SettingsConfigDict

from tcex_cli.app.config import InstallJson
from tcex_cli.cli.run.model.common_app_input_model import CommonAppInputModel
from tcex_cli.cli.run.model.common_model import CommonModel
from tcex_cli.cli.run.model.playbook_common_model import PlaybookCommonModel
from tcex_cli.cli.run.model.playbook_model import PlaybookModel


class AppPlaybookModel(CommonModel, PlaybookCommonModel, PlaybookModel):
    """Model Definition"""

    model_config = SettingsConfigDict(
        extra='allow',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        validate_assignment=True,
    )

    tc_playbook_out_variables: list[str] = InstallJson().tc_playbook_out_variables


class AppPlaybookInputModel(CommonAppInputModel):
    """Model Definition"""

    inputs: AppPlaybookModel
