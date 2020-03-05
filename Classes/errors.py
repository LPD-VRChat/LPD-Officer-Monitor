from discord.ext import commands

class NotReadyYet(commands.CheckFailure):
    """Exception raised when the bot is not ready yet.
    This inherits from :exc:`CheckFailure`
    """
    def __init__(self, message=None):
        super().__init__(message or 'I am still starting up, give me a moment.')

class WrongChannelForCommand(commands.CheckFailure):
    """Exception raised when a command is used in the wrong channel.
    This inherits from :exc:`CheckFailure`
    """
    def __init__(self, message=None):
        super().__init__(message or 'This command does not work in this channel.')

class ArgumentParsingError(Exception):
    """This exception is raised when the parser in argparse fails to parse a command and exits."""
    def __init__(self, message=None):
        super().__init__(message or 'Their is an issue in the ')