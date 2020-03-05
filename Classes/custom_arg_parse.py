import argparse
from sys import exc_info
import Classes.errors as errors

class ArgumentParser(argparse.ArgumentParser):
    def parse_args(self, *args, **kwargs):
        try: return super().parse_args(*args, **kwargs)
        except SystemExit as error:
            print("System exit excepted")
            print(error)
            raise errors.ArgumentParsingError("Something failed with parsing your command.")

    def _get_action_from_name(self, name):
        """Given a name, get the Action instance registered with this parser.
        If only it were made available in the ArgumentError object. It is 
        passed as it's first arg...
        """
        container = self._actions
        if name is None:
            return None
        for action in container:
            if '/'.join(action.option_strings) == name:
                return action
            elif action.metavar == name:
                return action
            elif action.dest == name:
                return action

    def error(self, message):
        exc = exc_info()[1]
        if exc:
            exc.argument = self._get_action_from_name(exc.argument_name)
            raise exc
        super(ArgumentParser, self).error(message)