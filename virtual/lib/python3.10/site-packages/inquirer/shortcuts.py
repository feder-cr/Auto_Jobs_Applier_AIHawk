import inquirer.questions as questions
from inquirer.render.console import ConsoleRender


def text(message, autocomplete=None, render=None, **kwargs):
    render = render or ConsoleRender()
    question = questions.Text(name="", message=message, autocomplete=autocomplete, **kwargs)
    return render.render(question)


def editor(message, render=None, **kwargs):
    render = render or ConsoleRender()
    question = questions.Editor(name="", message=message, **kwargs)
    return render.render(question)


def password(message, render=None, **kwargs):
    render = render or ConsoleRender()
    question = questions.Password(name="", message=message, **kwargs)
    return render.render(question)


def confirm(message, render=None, **kwargs):
    render = render or ConsoleRender()
    question = questions.Confirm(name="", message=message, **kwargs)
    return render.render(question)


def list_input(message, render=None, **kwargs):
    render = render or ConsoleRender()
    question = questions.List(name="", message=message, **kwargs)
    return render.render(question)


def checkbox(message, render=None, **kwargs):
    render = render or ConsoleRender()
    question = questions.Checkbox(name="", message=message, **kwargs)
    return render.render(question)


def path(message, render=None, **kwargs):
    render = render or ConsoleRender()
    question = questions.Path(name="", message=message, **kwargs)
    return render.render(question)
