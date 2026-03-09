from pydantic import BaseModel
from .page_actions import Action
from typing import List

class Page(BaseModel):
    url: str
    actions: List[Action]