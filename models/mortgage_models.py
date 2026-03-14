from pydantic import BaseModel
from typing import Dict, List

class FormData(BaseModel):
    formName: str
    data: Dict | List