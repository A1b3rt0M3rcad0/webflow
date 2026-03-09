from pydantic import BaseModel
from typing import Dict, Any, Union
from enum import Enum

class ActionType(Enum):
    GOTO = "goto"
    SCREENSHOT = "screenshot"
    TITLE = "title"
    CLICK = "click"
    FILL = "fill"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    GET_ELEMENT_DATA = "get_element_data"
    SOLVE_RECAPTCHA_V2_AND_INJECT = "solve_recaptcha_v2_and_inject"

class ElementDataType(Enum):
    TEXT = "text"
    HTML = "html"
    ATTRIBUTE = "attribute"
    VALUE = "value"

class RecaptchaVersion(Enum):
    V3 = "v3"
    V2 = "v2"

class Action(BaseModel):
    name: str
    params: Union[Dict[str, Any], None]

class GoToActionParams(BaseModel):
    url: str

class ScreenShotActionParams(BaseModel):
    path: str

class SolveNormalCaptchaActionParams(BaseModel):
    file: str

class SolveRecaptchaActionParams(BaseModel):
    version: RecaptchaVersion
    sitekey: str
    url: str

class ClickActionParams(BaseModel):
    selector: str
    force: bool = False

class FillActionParams(BaseModel):
    selector: str
    text: str
    delay: int | None = None

class WaitForSelectorActionParams(BaseModel):
    selector: str
    timeout: int | None = None

class GetElementDataActionParams(BaseModel):
    selector: str
    data_type: ElementDataType
    attribute_name: str | None = None


class SolveRecaptchaV2AndInjectParams(BaseModel):
    sitekey: str | None = None
    sitekey_selector: str | None = None  # ex: "[data-sitekey]" - obtém da página
    url: str | None = None  # se None, usa page.url
    max_retries: int = 3  # tentativas até conseguir resolver