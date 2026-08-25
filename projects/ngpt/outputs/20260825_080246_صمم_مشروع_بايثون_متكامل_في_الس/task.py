"""
task.py
=======
تعريف كلاس Task اللي بيحمل بيانات المهمة:
- أولوية (priority)
- عدد محاولات الإعادة (max_retries / retries)
- حالات المهمة (PENDING, RUNNING, SUCCESS, FAILED)
- دالة قابلة للتنفيذ (callable) محفوظة باسم عشان نقدر نخزّنها في SQLite
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, Optional


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# أولوية كلاسكية: كل ما الرقم أقل، كل ما المهمة أهم (زي PriorityQueue في heapq)
class Priority:
    HIGH = 1
    NORMAL = 5
    LOW = 9


# ريجستري للدوال المسموح بيها — كده نقدر نخزّن اسم الدالة في DB ونرجّعها عند التشغيل
TASK_REGISTRY: Dict[str, Callable[..., Any]] = {}


def register_task(name: str):
    """ديكوريتور لتسجيل أي دالة في الـ TASK_REGISTRY باسم معيّن."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        TASK_REGISTRY[name] = func
        return func

    return decorator


@dataclass
class Task:
    name: str                                  # اسم الدالة المسجّلة
    args: tuple = ()                           # Arguments للدالة
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: int = Priority.NORMAL
    max_retries: int = 3
    retries: int = 0
    status: TaskStatus = TaskStatus.PENDING
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    # --- Methods مساعدة ---
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # الـ Enum لازم يتسلسل كنص مش كائن
        data["status"] = self.status.value
        data["args"] = list(self.args)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        data = dict(data)
        data["status"] = TaskStatus(data.get("status", TaskStatus.PENDING.value))
        data["args"] = tuple(data.get("args", []))
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "Task":
        return cls.from_dict(json.loads(raw))

    def can_retry(self) -> bool:
        return self.retries < self.max_retries

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING

    def mark_success(self, result: Any) -> None:
        self.status = TaskStatus.SUCCESS
        try:
            self.result = json.dumps(result, ensure_ascii=False)
        except (TypeError, ValueError):
            self.result = str(result)

    def mark_failed(self, error: Exception) -> None:
        self.error = f"{type(error).__name__}: {error}"
        if self.can_retry():
            self.status = TaskStatus.PENDING
            self.retries += 1
        else:
            self.status = TaskStatus.FAILED

    def execute(self) -> Any:
        """بتنفّذ الدالة المسجّلة باسم الـ name."""
        if self.name not in TASK_REGISTRY:
            raise KeyError(f"Task '{self.name}' is not registered.")
        func = TASK_REGISTRY[self.name]
        return func(*self.args, **self.kwargs)
