from __future__ import annotations

from pydantic import BaseModel
from typing import List


class Task(BaseModel):
    task: str
    data: str


class TaskIn(BaseModel):
    task_list: List[Task]
