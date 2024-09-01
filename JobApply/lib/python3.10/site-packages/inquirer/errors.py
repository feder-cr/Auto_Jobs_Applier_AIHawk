class ValidationError(Exception):
    def __init__(self, value, reason=None, *args):
        super().__init__(*args)
        self.value = value
        self.reason = reason


class UnknownQuestionTypeError(Exception):
    pass


class EndOfInput(Exception):
    def __init__(self, selection, *args):
        super().__init__(*args)
        self.selection = selection


class ThemeError(AttributeError):
    pass
