"""TcEx Framework Module"""

# first-party
from tcex_cli.app.config import AppSpecYml
from tcex_cli.app.config.model import TcexJsonModel
from tcex_cli.cli.cli_abc import CliABC
from tcex_cli.render.render import Render


class GenTcexJson(CliABC):
    """Generate App Config File"""

    def __init__(self, asy: AppSpecYml):
        """Initialize instance properties."""
        super().__init__()
        self.asy = asy

        # properties
        self.filename = 'tcex.json'

    def generate(self):
        """Generate the layout.json file data."""

        try:
            tcex_json_data = self.app.tj.model.dict()
        except ValueError as ex:
            Render.panel.failure(f'Failed to load {self.filename} file.\n\n{ex}')

        # update package name
        tcex_json_data['package']['app_name'] = self.asy.model.package_name
        return TcexJsonModel(**tcex_json_data)
