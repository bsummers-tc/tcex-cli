"""TcEx Framework Module"""

from pydantic import BaseModel, ConfigDict, field_validator
from semantic_version import Version


class TemplateConfigModel(BaseModel):
    """Model definition for template.yaml configuration file"""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    contributor: str
    description: str
    name: str
    summary: str
    template_files: list[str] | None = []
    template_parents: list[str] = []
    type: str
    version: Version

    @field_validator('version', mode='before')
    @classmethod
    def version_validator(cls, v):
        """Return a version object for "version" fields."""
        if v is not None:
            return Version(v)
        return v

    @property
    def install_command(self) -> str:
        """Return the install command for the template."""
        return f'tcex init --type {self.type} --template {self.name}'
