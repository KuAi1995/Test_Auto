"""核心数据模型."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TestPriority(str, Enum):
    """测试优先级."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TestStatus(str, Enum):
    """测试执行状态."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestType(str, Enum):
    """测试类型."""

    UNIT = "unit"
    MANUAL = "manual"
    UI = "ui"
    STABILITY = "stability"
    OPENCV = "opencv"


class TestStep(BaseModel):
    """测试步骤."""

    action: str
    expected: str = ""


class TestCase(BaseModel):
    """测试用例."""

    id: str = ""
    title: str
    module: str = ""
    test_type: TestType = TestType.MANUAL
    priority: TestPriority = TestPriority.P1
    precondition: str = ""
    steps: list[TestStep] = Field(default_factory=list)
    automated: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TestResult(BaseModel):
    """测试执行结果."""

    id: str = ""
    run_id: str = ""
    case_id: str = ""
    status: TestStatus = TestStatus.PENDING
    duration_ms: int = 0
    message: str = ""
    screenshot: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.now)


class ClassInfo(BaseModel):
    """代码分析 - 类信息."""

    name: str
    package: str = ""
    file_path: str = ""
    superclass: str = ""
    interfaces: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    is_abstract: bool = False
    is_activity: bool = False
    is_fragment: bool = False


class MethodInfo(BaseModel):
    """代码分析 - 方法信息."""

    name: str
    class_name: str = ""
    return_type: str = "void"
    params: list[str] = Field(default_factory=list)
    is_public: bool = True
    is_static: bool = False
    line_start: int = 0
    line_end: int = 0
