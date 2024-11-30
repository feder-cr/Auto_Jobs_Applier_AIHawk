from enum import Enum

from attr import dataclass


class TextBoxQuestionType(Enum):
    NUMERIC = "numeric"
    TEXTBOX = "textbox"


@dataclass
class RadioQuestion:
    question: str
    options: list[str]


@dataclass
class TextBoxQuestion:
    question: str
    type: TextBoxQuestionType
    is_cover_letter: bool
