# Standard
import argparse
import sys
from io import StringIO

# Mine
import Classes.errors as errors


class ArgumentParser(argparse.ArgumentParser):
    def parse_args(self, command_name, *args, **kwargs):

        # Store the reference and make a new variable that will receive stderr
        old_stderr = sys.stderr
        result = StringIO()
        sys.stderr = result

        # Parse the args
        try:
            return super().parse_args(*args, **kwargs)
        except SystemExit:
            result_string = "\n" + result.getvalue().replace("main.py: ", "").replace(
                "main.py", command_name
            )
            raise errors.ArgumentParsingError(result_string)
        finally:
            # Redirect stderr back to the screen
            sys.stderr = old_stderr

    def _get_action_from_name(self, name):
        """Given a name, get the Action instance registered with this parser.
        If only it were made available in the ArgumentError object. It is
        passed as it's first arg...
        """
        container = self._actions
        if name is None:
            return None
        for action in container:
            if "/".join(action.option_strings) == name:
                return action
            elif action.metavar == name:
                return action
            elif action.dest == name:
                return action

    def error(self, message):
        exc = sys.exc_info()[1]
        if exc:
            exc.argument = self._get_action_from_name(exc.argument_name)
            raise exc
        super(ArgumentParser, self).error(message)
