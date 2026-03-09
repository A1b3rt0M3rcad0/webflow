from pydantic import BaseModel
from typing import List
from .browser import Browser

class Workflow(BaseModel):
    browsers: List[Browser]