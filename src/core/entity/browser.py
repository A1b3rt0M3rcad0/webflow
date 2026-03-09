from typing import List
from enum import Enum
from .page import Page
from pydantic import BaseModel

class BrowserType(Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"

class Browser(BaseModel):
    btype: BrowserType
    pages: List["Page"]