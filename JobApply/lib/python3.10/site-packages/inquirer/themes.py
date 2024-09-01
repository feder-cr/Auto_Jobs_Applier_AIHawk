import collections
import json

from blessed import Terminal

import inquirer.errors as errors


term = Terminal()


def load_theme_from_json(json_theme):
    """Load a theme from a json.

    Expected format:
        >>> {
        ...     "Question": {
        ...         "mark_color": "yellow",
        ...         "brackets_color": "normal",
        ...         ...
        ...     },
        ...     "List": {
        ...         "selection_color": "bold_blue",
        ...         "selection_cursor": "->"
        ...     }
        ... }

    Color values should be string representing valid blessings.Terminal colors.
    """
    return load_theme_from_dict(json.loads(json_theme))


def load_theme_from_dict(dict_theme):
    """Load a theme from a dict.

    Expected format:
        >>> {
        ...     "Question": {
        ...         "mark_color": "yellow",
        ...         "brackets_color": "normal",
        ...         ...
        ...     },
        ...     "List": {
        ...         "selection_color": "bold_blue",
        ...         "selection_cursor": "->"
        ...     }
        ... }

    Color values should be string representing valid blessings.Terminal colors.
    """
    t = Default()
    for question_type, settings in dict_theme.items():
        if question_type not in vars(t):
            raise errors.ThemeError(
                "Error while parsing theme. Question type " "`{}` not found or not customizable.".format(question_type)
            )

        # calculating fields of namedtuple, hence the filtering
        question_fields = list(filter(lambda x: not x.startswith("_"), vars(getattr(t, question_type))))

        for field, value in settings.items():
            if field not in question_fields:
                raise errors.ThemeError(
                    "Error while parsing theme. Field "
                    "`{}` invalid for question type `{}`".format(field, question_type)
                )
            actual_value = getattr(term, value) or value
            setattr(getattr(t, question_type), field, actual_value)
    return t


class Theme:
    def __init__(self):
        self.Question = collections.namedtuple("question", "mark_color brackets_color default_color")
        self.Editor = collections.namedtuple("editor", "opening_prompt")
        self.Checkbox = collections.namedtuple(
            "common",
            "selection_color selection_icon selected_color unselected_color "
            "selected_icon unselected_icon locked_option_color",
        )
        self.List = collections.namedtuple("List", "selection_color selection_cursor unselected_color")


class Default(Theme):
    def __init__(self):
        super().__init__()
        self.Question.mark_color = term.yellow
        self.Question.brackets_color = term.normal
        self.Question.default_color = term.normal
        self.Editor.opening_prompt_color = term.bright_black
        self.Checkbox.selection_color = term.cyan
        self.Checkbox.selection_icon = ">"
        self.Checkbox.selected_icon = "[X]"
        self.Checkbox.selected_color = term.yellow + term.bold
        self.Checkbox.unselected_color = term.normal
        self.Checkbox.unselected_icon = "[ ]"
        self.Checkbox.locked_option_color = term.gray50
        self.List.selection_color = term.cyan
        self.List.selection_cursor = ">"
        self.List.unselected_color = term.normal


class GreenPassion(Default):
    def __init__(self):
        super().__init__()
        self.Question.brackets_color = term.bright_green
        self.Checkbox.selection_color = term.bold_black_on_bright_green
        self.Checkbox.selection_icon = "❯"
        self.Checkbox.selected_icon = "◉"
        self.Checkbox.selected_color = term.green
        self.Checkbox.unselected_icon = "◯"
        self.List.selection_color = term.bold_black_on_bright_green
        self.List.selection_cursor = "❯"


class BlueComposure(Default):
    def __init__(self):
        super().__init__()
        self.Question.brackets_color = term.dodgerblue
        self.Question.default_color = term.deepskyblue2
        self.Checkbox.selection_icon = "➤"
        self.Checkbox.selection_color = term.bold_black_on_darkslategray3
        self.Checkbox.selected_icon = "☒"
        self.Checkbox.selected_color = term.cyan3
        self.Checkbox.unselected_icon = "☐"
        self.List.selection_color = term.bold_black_on_darkslategray3
        self.List.selection_cursor = "➤"
