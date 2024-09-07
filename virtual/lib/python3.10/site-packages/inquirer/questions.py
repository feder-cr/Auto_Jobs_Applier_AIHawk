"""Module that implements the questions types."""

from __future__ import annotations

import json
import pathlib

import inquirer.errors as errors
from inquirer.render.console._other import GLOBAL_OTHER_CHOICE


class TaggedValue:
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value
        self.tuple = (tag, value)

    def __str__(self):
        return self.tag

    def __repr__(self):
        return repr(self.value)

    def __eq__(self, other):
        if isinstance(other, TaggedValue):
            return other.value == self.value
        if isinstance(other, tuple):
            return other == self.tuple
        return other == self.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.tuple)


class Question:
    kind = "base question"

    def __init__(
        self,
        name,
        message="",
        choices=None,
        default=None,
        ignore=False,
        validate=True,
        show_default=False,
        hints=None,
        other=False,
    ):
        self.name = name
        self._message = message
        self._choices = choices or []
        self._default = default
        self._ignore = ignore
        self._validate = validate
        self.answers = {}
        self.show_default = show_default
        self.hints = hints
        self._other = other

        if self._other:
            self._choices.append(GLOBAL_OTHER_CHOICE)

    def add_choice(self, choice):
        try:
            index = self._choices.index(choice)
            return index
        except ValueError:
            if self._other:
                self._choices.insert(-1, choice)
                return len(self._choices) - 2

            self._choices.append(choice)
            return len(self._choices) - 1

    @property
    def ignore(self):
        return bool(self._solve(self._ignore))

    @property
    def message(self):
        return self._solve(self._message)

    @property
    def default(self):
        return self.answers.get(self.name) or self._solve(self._default)

    @property
    def choices_generator(self):
        for choice in self._solve(self._choices):
            yield (TaggedValue(*choice) if isinstance(choice, tuple) and len(choice) == 2 else choice)

    @property
    def choices(self):
        return list(self.choices_generator)

    def validate(self, current):
        try:
            if self._solve(self._validate, current):
                return
        except errors.ValidationError as e:
            raise e
        raise errors.ValidationError(current)

    def _solve(self, prop, *args, **kwargs):
        if callable(prop):
            return prop(self.answers, *args, **kwargs)
        if isinstance(prop, str):
            return prop.format(**self.answers)
        return prop


class Text(Question):
    kind = "text"

    def __init__(self, name, message="", default=None, autocomplete=None, **kwargs):
        super().__init__(
            name, message=message, default=str(default) if default and not callable(default) else default, **kwargs
        )
        self.autocomplete = autocomplete


class Password(Text):
    kind = "password"

    def __init__(self, name, echo="*", **kwargs):
        super().__init__(name, **kwargs)
        self.echo = echo


class Editor(Text):
    kind = "editor"


class Confirm(Question):
    kind = "confirm"

    def __init__(self, name, default=False, **kwargs):
        super().__init__(name, default=default, **kwargs)


class List(Question):
    kind = "list"

    def __init__(
        self,
        name,
        message="",
        choices=None,
        hints=None,
        default=None,
        ignore=False,
        validate=True,
        carousel=False,
        other=False,
        autocomplete=None,
    ):
        super().__init__(name, message, choices, default, ignore, validate, hints=hints, other=other)
        self.carousel = carousel
        self.autocomplete = autocomplete


class Checkbox(Question):
    kind = "checkbox"

    def __init__(
        self,
        name,
        message="",
        choices=None,
        hints=None,
        locked=None,
        default=None,
        ignore=False,
        validate=True,
        carousel=False,
        other=False,
        autocomplete=None,
    ):
        super().__init__(name, message, choices, default, ignore, validate, hints=hints, other=other)
        self.locked = locked
        self.carousel = carousel
        self.autocomplete = autocomplete


class Path(Text):
    ANY = "any"
    FILE = "file"
    DIRECTORY = "directory"

    kind = "path"

    def __init__(self, name, default=None, path_type="any", exists=None, **kwargs):
        super().__init__(name, default=default, **kwargs)

        if path_type in (Path.ANY, Path.FILE, Path.DIRECTORY):
            self._path_type = path_type
        else:
            raise ValueError("'path_type' must be one of [ANY, FILE, DIRECTORY]")

        self._exists = exists

        if default is not None:
            try:
                self.validate(default)
            except errors.ValidationError:
                raise ValueError("Default value '{}' is not valid based on " "your Path's criteria".format(default))

    def validate(self, current: str):
        super().validate(current)

        if current is None:
            raise errors.ValidationError(current)

        path = pathlib.Path(current)

        # this block validates the path in correspondence with the OS
        # it will error if the path contains invalid characters
        try:
            path.lstat()
        except FileNotFoundError:
            pass
        except (ValueError, OSError) as e:
            raise errors.ValidationError(e)

        if (self._exists is True and not path.exists()) or (self._exists is False and path.exists()):
            raise errors.ValidationError(current)

        # os.path.isdir and isfile check also existence of the path,
        # which might not be desirable
        if self._path_type == Path.FILE:
            if current.endswith(("\\", "/")):
                raise errors.ValidationError(current)
            if path.exists() and not path.is_file():
                raise errors.ValidationError(current)

        if self._path_type == Path.DIRECTORY:
            if current == "":
                raise errors.ValidationError(current)
            if path.exists() and not path.is_dir():
                raise errors.ValidationError(current)


def question_factory(kind, *args, **kwargs):
    for cl in (Text, Editor, Password, Confirm, List, Checkbox, Path):
        if cl.kind == kind:
            return cl(*args, **kwargs)
    raise errors.UnknownQuestionTypeError()


def load_from_dict(question_dict) -> Question:
    """Load one question from a dict.

    It requires the keys 'name' and 'kind'.

    Returns:
        The Question object with associated data.
    """
    return question_factory(**question_dict)


def load_from_list(question_list) -> list[Question]:
    """Load a list of questions from a list of dicts.

    It requires the keys 'name' and 'kind' for each dict.

    Returns:
        A list of Question objects with associated data.
    """
    return [load_from_dict(q) for q in question_list]


def load_from_json(question_json) -> list | dict:
    """Load Questions from a JSON string.

    Returns:
        A list of Question objects with associated data if the JSON
        contains a list or a Question if the JSON contains a dict.
    """
    data = json.loads(question_json)
    if isinstance(data, list):
        return load_from_list(data)
    if isinstance(data, dict):
        return load_from_dict(data)
    raise TypeError("Json contained a %s variable when a dict or list was expected", type(data))
