from dataclasses import dataclass
from typing import Optional, Union


@dataclass(frozen=True)
class Print:
    value: str


@dataclass(frozen=True)
class Input:
    prompt: Optional[str]
    user_input: Union[EOFError, KeyboardInterrupt, str]
