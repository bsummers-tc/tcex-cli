"""Bin Testing"""

# third-party
import pytest
from click.testing import Result
from typer.testing import CliRunner

# first-party
from tcex_cli.cli.cli import app

# get instance of typer CliRunner for test case
runner = CliRunner()


@pytest.mark.run(order=2)
class TestTcexCliList:
    """Tcex CLI Testing."""

    def setup_method(self):
        """Configure setup before all tests."""

    def teardown_method(self):
        """Configure teardown before all tests."""

    @staticmethod
    def _run_command(args: list[str]) -> Result:
        """Test Case"""
        result = runner.invoke(app, args)
        return result

    def test_tcex_list(self):
        """Test Case"""
        result = self._run_command(['list'])
        assert result.exit_code == 0, result.stdout

        # spot check a few lines of outputs
        assert 'Organization Templates' in result.stdout
        assert 'Playbook Templates' in result.stdout

        # TODO: [med] update this once template is done
        # assert 'API Service Templates' in result.stdout
        # assert 'Trigger Service Templates' in result.stdout
        # assert 'Webhook Trigger Service Templates' in result.stdout

    # TODO: [med] update this once template is done
    # def test_tcex_list_external_api_service(self):
    #     """Test Case"""
    #     result = self._run_command(['list', '--type', 'api_service'])
    #     assert result.exit_code == 0, result.stdout

    #     # spot check a few lines of outputs
    #     assert 'basic' in result.stdout

    # TODO: [med] update this once template is done
    # def test_tcex_list_external_basic(self):
    #     """Test Case"""
    #     result = self._run_command(['list', '--type', 'external'])
    #     assert result.exit_code == 0, result.stdout

    #     # spot check a few lines of outputs
    #     assert 'basic' in result.stdout

    def test_tcex_list_organization_basic(self):
        """Test Case"""
        result = self._run_command(['list', '--type', 'organization'])
        assert result.exit_code == 0, result.stdout

        # spot check a few lines of outputs
        assert 'basic' in result.stdout

    def test_tcex_list_playbook_basic(self):
        """Test Case"""
        result = self._run_command(['list', '--type', 'playbook'])
        assert result.exit_code == 0, f'{result.stdout}'

        # spot check a few lines of outputs
        assert 'basic' in result.stdout

    # TODO: [med] update this once template is done
    # def test_tcex_list_trigger_basic(self):
    #     """Test Case"""
    #     result = self._run_command(['list', '--type', 'trigger_service'])
    #     assert result.exit_code == 0, result.stdout

    #     # spot check a few lines of outputs
    #     assert 'basic' in result.stdout

    # TODO: [med] update this once template is done
    # def test_tcex_list_webhook_trigger_basic(self):
    #     """Test Case"""
    #     result = self._run_command(['list', '--type', 'webhook_trigger_service'])
    #     assert result.exit_code == 0, result.stdout

    #     # spot check a few lines of outputs
    #     assert 'basic' in result.stdout
