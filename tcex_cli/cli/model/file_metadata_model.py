"""TcEx Framework Module"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class FileMetadataModel(BaseModel):
    """Model Definition"""

    model_config = ConfigDict(extra='allow')

    download_url: str | None = Field(
        None, description='The download url for the file. Directories will not have a download url.'
    )
    name: str = Field(..., description='The name of the file.')
    path: str = Field(..., description='The path of the file.')
    sha: str = Field(..., description='The sha of the file.')
    url: str = Field(..., description='The url of the file.')
    type: str = Field(..., description='The type (dir or file).')

    # local metadata
    relative_path: Path = Field(
        default=Path('tmp'),
        description='The relative path of the file. This is the path from the root of the repo.',
    )
    template_name: str
    template_type: str
