"""TcEx Framework Module"""

# third-party
import typer

# first-party
from tcex_cli.cli.validate.validate_cli import ValidateCli
from tcex_cli.render.render import Render


def command(
    app_builder: bool = typer.Option(
        False, help='(Advanced) If true, this command was run from App Builder.'
    ),
    ignore_validation: bool = typer.Option(
        False, help='If true, validation errors will not cause an exit.'
    ),
):
    """Run validation of the current App.

    Validations:
    * validate Python files have valid syntax
    * validate install.json has valid syntax
    * validate layout.json has valid syntax
    * validate the feed files are valid
    """
    cli = ValidateCli(ignore_validation)
    try:
        cli.update_system_path()
        # run in interactive
        if app_builder:
            cli.interactive()
        else:
            cli.check_syntax()
            cli.check_install_json()
            cli.check_layout_json()
            cli.check_job_json()

            # render results
            Render.table_validation_summary(
                'File Syntax Validation', cli.validation_data.fileSyntax
            )
            Render.table_validation_summary('Config Schema Validation', cli.validation_data.schema_)
            Render.table_validation_summary('Layout Validation', cli.validation_data.layouts)
            Render.table_validation_summary('Feeds Validation', cli.validation_data.feeds)
            Render.panel.list('Validation Errors', cli.validation_data.errors, 'bold red')
    except Exception as ex:
        cli.log.exception('Failed to run "tcex validation" command.')
        Render.panel.failure(f'Exception: {ex}')
