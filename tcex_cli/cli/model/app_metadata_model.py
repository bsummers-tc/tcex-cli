"""TcEx Framework Module"""

# third-party
from pydantic import BaseModel


class AppMetadataModel(BaseModel):
    """Model Definition"""

    name: str
    package_name: str
    template_directory: str
    version: str
