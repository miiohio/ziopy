from typing import Any

import pytest
from zio_py.runtime import Runtime


@pytest.fixture
def simple_runtime() -> Runtime[Any]:
    return Runtime()
