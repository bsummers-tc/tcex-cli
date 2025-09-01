"""TcEx Framework Module"""

import typer

from tcex_cli.cli.app_input.app_input_cli import AppInputCli
from tcex_cli.render.render import Render


def command(
    include_optional: bool = typer.Option(
        default=False, help='If true optional parameters will be included.'
    ),
):
    """Build app_inputs.json file from the app's install.json file."""
    cli = AppInputCli(include_optional)
    try:
        # generate app_inputs.json
        cli.generate_app_inputs()

        Render.panel.success('Completed successfully.')
    except Exception as ex:
        cli.log.exception('Failed to run "tcex deps" command.')
        Render.panel.failure(f'Exception: {ex}')
