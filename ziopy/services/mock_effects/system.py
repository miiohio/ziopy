from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Exit:
    exit_code: Optional[int]
