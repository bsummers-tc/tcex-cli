"""TcEx Framework Module"""

# first-party
from tcex_cli.app.config import AppSpecYml
from tcex_cli.app.config.model.job_json_model import JobJsonModel
from tcex_cli.cli.cli_abc import CliABC


class GenJobJson(CliABC):
    """Generate App Config File"""

    def __init__(self, asy: AppSpecYml):
        """Initialize instance properties."""
        super().__init__()
        self.asy = asy

    def generate(self):
        """Generate the layout.json file data."""
        if (
            self.asy.model.is_feed_app
            and self.asy.model.organization
            and self.asy.model.organization.feeds
        ):
            for feed in self.asy.model.organization.feeds:
                _job_data = feed.job.dict(by_alias=True)
                app_name = self.app.tj.model.package.app_name.replace('_', ' ')

                # handle statically defined version in tcex.json file
                version = f'v{self.asy.model.program_version.major}'
                if self.app.tj.model.package.app_version:
                    version = self.app.tj.model.package.app_version

                _job_data['programName'] = f'{app_name} {version}'
                _job_data['programVersion'] = str(self.asy.model.program_version)
                yield feed.job_file, JobJsonModel(**_job_data)
