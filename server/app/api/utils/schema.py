from __future__ import annotations

from pydantic import BaseModel
from typing import Any


class TaskIn(BaseModel):
    task: str
    dataIn: Any = None


