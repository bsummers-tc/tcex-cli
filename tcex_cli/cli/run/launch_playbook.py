"""Run App Local"""
# standard library
import base64
import binascii
import json
import sys
from pathlib import Path, PosixPath

# first-party
from tcex_cli.cli.run.launch_abc import LaunchABC
from tcex_cli.cli.run.model.app_playbook_model import AppPlaybookModel
from tcex_cli.cli.run.playbook_create import (
    KEY_VALUE_KEYS,
    TC_ENTITY_KEYS,
    PlaybookCreate,
    StagedVariable,
)
from tcex_cli.input.field_type.sensitive import Sensitive
from tcex_cli.pleb.cached_property import cached_property
from tcex_cli.render.render import Render


class LaunchPlaybook(LaunchABC):
    """Launch an App"""

    def __init__(self, config_json: Path):
        """Initialize class properties."""
        super().__init__(config_json)
        self.playbook = PlaybookCreate(self.redis_client, self.inputs.tc_playbook_kvstore_context)

    @cached_property
    def inputs(self) -> AppPlaybookModel:
        """Return the App inputs."""
        app_inputs = {}
        if self.config_json.is_file():
            with self.config_json.open('r', encoding='utf-8') as fh:
                try:
                    app_inputs = json.load(fh)
                except ValueError as ex:
                    print(f'Error loading app_inputs.json: {ex}')
                    sys.exit(1)

        return AppPlaybookModel(**app_inputs)

    @cached_property
    def ij(self) -> dict:
        """Return the Install.json model."""
        install_json = Path('install.json')
        if not install_json.is_file():
            sys.exit(1)
        with install_json.open('r', encoding='utf-8') as fh:
            return json.load(fh)

    @cached_property
    def ij_key_types_map(self) -> dict[str, list[str]]:
        """Return the Install.json key types map."""
        return {
            p.get('name'): p.get('playbookDataType', ['String']) for p in self.ij.get('params', [])
        }

    def get_kvstore_type(self, value, is_list=False):
        """Return the kvstore type for the provided value."""
        type_ = None
        if isinstance(value, list) and value:
            return self.get_kvstore_type(value[0], is_list=True)
        if isinstance(value, dict):
            if all(x in value for x in TC_ENTITY_KEYS):
                type_ = 'TCEntity'
            elif all(x in value for x in KEY_VALUE_KEYS):
                type_ = 'KeyValue'
        elif isinstance(value, (str, int, bool)):
            type_ = 'String'
        elif isinstance(value, bytes):
            type_ = 'Binary'
        if is_list and type_:
            type_ += 'Array'
        return type_

    def construct_staged_name(self, field_name: str, field_value) -> StagedVariable | None:
        """Construct the staged variable name."""
        if field_value is None:
            return None
        value = self.get_kvstore_type(field_value)
        if value:
            return StagedVariable(field_name, value)
        return StagedVariable(field_name, (self.ij_key_types_map.get(field_name) or ['String'])[0])

    def stage_variable(self, staged_variable: StagedVariable, value):
        """Stage the variable in redis."""
        self.log.info(f'step=stage, data=from-dict, variable={staged_variable}, value={value}')
        data = value
        if value is not None and staged_variable.type == 'Binary':
            data = self._decode_binary(value, staged_variable)
        elif value is not None and staged_variable.type == 'BinaryArray':
            data = [self._decode_binary(d, staged_variable) for d in value]
        self.playbook.any(staged_variable, data)

    @cached_property
    def inputs_staged(self) -> dict:
        """Return the App inputs with their values staged in redis."""
        app_inputs = {}
        for field_name, field_value in self.inputs:
            staged_name = self.construct_staged_name(field_name, field_value)
            app_inputs[field_name] = field_value
            if staged_name:
                app_inputs[field_name] = str(staged_name)
                self.stage_variable(staged_name, field_value)
            elif isinstance(field_value, PosixPath) and field_value:
                app_inputs[field_name] = str(field_value)
            elif isinstance(field_value, Sensitive) and field_value:
                app_inputs[field_name] = str(field_value.value)

        return app_inputs

    def print_input_data(self):
        """Print the inputs."""
        input_data = self.live_format_dict(self.inputs.dict()).strip()
        Render.panel.info(f'{input_data}', f'[{self.panel_title}]Input Data[/]')

    def print_output_data(self):
        """Log the playbook output data."""
        output_data = self.live_format_dict(
            self.output_data(self.inputs.tc_playbook_kvstore_context)
        ).strip()
        Render.panel.info(f'{output_data}', f'[{self.panel_title}]Output Data[/]')

    @staticmethod
    def _decode_binary(binary_data, variable):
        """Base64 decode binary data."""
        try:
            data = None
            if binary_data is not None:
                data = base64.b64decode(binary_data)
        except binascii.Error as e:
            print(
                f'The Binary staging data for variable {variable} '
                f'is not properly base64 encoded due to {e}.'
            )
            sys.exit()
        return data
