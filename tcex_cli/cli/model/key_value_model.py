"""TcEx Framework Module"""

from pydantic import BaseModel


class KeyValueModel(BaseModel):
    """Model Definition"""

    key: str
    value: str
