from enum import Enum

from attr import dataclass


class TextBoxQuestionType(Enum):
    NUMERIC = "numeric"
    TEXTBOX = "textbox"

class SelectQuestionType(Enum):
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"

@dataclass
class SelectQuestion:
    question: str
    options: list[str]
    type: SelectQuestionType


@dataclass
class TextBoxQuestion:
    question: str
    type: TextBoxQuestionType
