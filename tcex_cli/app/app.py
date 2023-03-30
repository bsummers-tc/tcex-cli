"""TcEx Framework Module"""

# first-party
from tcex_cli.app.config.install_json import InstallJson
from tcex_cli.app.config.job_json import JobJson
from tcex_cli.app.config.layout_json import LayoutJson
from tcex_cli.app.config.permutation import Permutation
from tcex_cli.app.config.tcex_json import TcexJson
from tcex_cli.pleb.cached_property import cached_property


class App:
    """TcEx Module"""

    def __init__(self):
        """Initialize instance properties."""

    def clear_cache(self):
        """Clear the cache."""
        if hasattr(self, '_ij'):
            del self.__dict__['_ij']
        if hasattr(self, '_jj'):
            del self.__dict__['_jj']
        if hasattr(self, '_lj'):
            del self.__dict__['_lj']
        if hasattr(self, '_tj'):
            del self.__dict__['_tj']

    @cached_property
    def ij(self) -> InstallJson:
        """Return the install.json file as a dict."""
        return self.install_json

    @cached_property
    def install_json(self) -> InstallJson:
        """Return the install.json file as a dict."""
        return InstallJson()

    @cached_property
    def jj(self) -> JobJson:
        """Return the job.json file as a dict."""
        return self.job_json

    @cached_property
    def job_json(self) -> JobJson:
        """Return the job.json file as a dict."""
        return JobJson()

    @cached_property
    def layout_json(self) -> LayoutJson:
        """Return the layout.json file as a dict."""
        return LayoutJson()

    @cached_property
    def lj(self) -> LayoutJson:
        """Return the layout.json file as a dict."""
        return self.layout_json

    @cached_property
    def permutation(self) -> Permutation:
        """Return the permutation file as a dict."""
        return Permutation()

    @cached_property
    def tcex_json(self) -> TcexJson:
        """Return the tcex.json file as a dict."""
        return TcexJson()

    @cached_property
    def tj(self) -> TcexJson:
        """Return the tcex.json file as a dict."""
        return self.tcex_json

    @cached_property
    def user_agent(self) -> dict[str, str]:
        """Return a User-Agent string."""
        return {
            'User-Agent': (
                f'TcExCli/{__import__(__name__).__version__}, '
                f'{self.ij.model.display_name}/{self.ij.model.program_version}'
            )
        }
