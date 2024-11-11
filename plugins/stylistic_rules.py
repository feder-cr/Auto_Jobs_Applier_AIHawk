import astroid
from pylint.checkers import BaseChecker


class BlankLineChecker(BaseChecker):
    """
    A custom Pylint checker to enforce custom blank line rules.

    Fields:
        name (str): The name of the checker.
        priority (int): The priority of the checker. Lower numbers indicate higher priority.
        msgs (dict): A dictionary mapping message IDs to their corresponding message details.

    Messages:
        C9001: Missing blank line before an if-statement.
        C9002: Missing blank line before a while-loop.
        C9003: Missing blank line before a for-loop.
        C9004: Missing blank line before a try-block.

    Methods:
        visit_if(node): Checks for a blank line before an if-statement.
        visit_while(node): Checks for a blank line before a while-loop.
        visit_for(node): Checks for a blank line before a for-loop.
        visit_try(node): Checks for a blank line before a try-block.

    Example:
        To use this checker, register it with Pylint by adding it to your `.pylintrc` file
        or by loading it as a plugin in your Pylint configuration.

        ```python
        def register(linter):
            linter.register_checker(BlankLineChecker(linter))
        ```
    """

    name = "blank-line-checker"
    priority = -1
    msgs = {
        "C9001": (
            "Missing blank line before if-statement.",
            "blank-line-before-if",
            "Ensure there is a blank line before if-statements, except when they are at the \
                beginning of method definitions.",
        ),
        "C9002": (
            "Missing blank line before while-loop.",
            "blank-line-before-while",
            "Ensure there is a blank line before while-loops, except when they are at the \
                beginning of method definitions.",
        ),
        "C9003": (
            "Missing blank line before for-loop.",
            "blank-line-before-for",
            "Ensure there is a blank line before for-loops, except when they are at the beginning \
                of method definitions.",
        ),
        "C9004": (
            "Missing blank line before try-block.",
            "blank-line-before-try",
            "Ensure there is a blank line before try-blocks, except when they are at the beginning \
                of method definitions.",
        ),
    }

    def visit_if(self, node):
        """Checks for a blank line before an if-statement."""
        self._check_blank_line(node, "blank-line-before-if")

    def visit_while(self, node):
        """Checks for a blank line before a while-loop."""
        self._check_blank_line(node, "blank-line-before-while")

    def visit_for(self, node):
        """Checks for a blank line before a for-loop."""
        self._check_blank_line(node, "blank-line-before-for")

    def visit_try(self, node):
        """Checks for a blank line before a try-block."""
        self._check_blank_line(node, "blank-line-before-try")

    def _check_blank_line(self, node, msg_id):
        """
        Helper function to check if there's a blank line or appropriate block above the node.

        Args:
            node (astroid.NodeNG): The current AST node being checked.
            msg_id (str): The message ID to be emitted if the rule is violated.

        """
        prev_node = node.previous_sibling()

        if prev_node is None:
            return

        if isinstance(prev_node, (astroid.FunctionDef, astroid.ClassDef)):
            return

        if isinstance(prev_node, astroid.Const) and isinstance(prev_node.value, str):
            return

        prev_lineno = prev_node.lineno
        current_lineno = node.lineno

        if current_lineno - prev_lineno <= 1:
            self.add_message(msg_id, node=node)


def register(linter):
    """Required method to auto-register this checker."""
    linter.register_checker(BlankLineChecker(linter))
