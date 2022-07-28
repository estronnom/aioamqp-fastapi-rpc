from __future__ import annotations

from pydantic import BaseModel
from typing import Any


class TaskIn(BaseModel):
    task: str
    response: bool = True
    dataIn: Any = None


class TaskOut(BaseModel):
    sent: bool = None
    success: bool = None
    response: None | dict = None
