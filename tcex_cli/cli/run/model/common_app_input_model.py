"""TcEx Framework Module"""
# standard library
from typing import Any

# third-party
from pydantic import BaseModel


class StageModel(BaseModel):
    """Model Definition"""

    kvstore: dict[str, str | dict | list[str | dict]] = {}


class CommonAppInputModel(BaseModel):
    """Model Definition"""

    stage: StageModel
    trigger_inputs: list[dict] = []
    inputs: Any
