"""TcEx Framework Module"""

from pydantic import ConfigDict

from .api_model import ApiModel
from .proxy_model import ProxyModel


class ModuleRequestsSessionModel(ApiModel, ProxyModel):
    """Model Definition

    This model provides all the inputs required by the "tcex.requests_tc" module.
    """

    model_config = ConfigDict(extra='ignore')
