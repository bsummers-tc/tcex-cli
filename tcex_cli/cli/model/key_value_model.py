"""TcEx Framework Module"""

# third-party
from pydantic import BaseModel


class KeyValueModel(BaseModel):
    """Model Definition"""

    key: str
    value: str
