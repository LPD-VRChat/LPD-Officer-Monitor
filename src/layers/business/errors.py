from discord.ext import commands


class NotReadyYet(commands.CheckFailure):
    """Exception raised when the bot is not ready yet.
    This inherits from :exc:`CheckFailure`
    """

    def __init__(self, message=None):
        super().__init__(message or "I am still starting up, give me a moment.")


class WrongChannelError(commands.CheckFailure):
    """Exception raised when a command is used in the wrong channel.
    This inherits from :exc:`CheckFailure`
    """

    def __init__(self, message=None):
        super().__init__(message or "This command does not work in this channel.")


class NotForYouError(commands.CheckFailure):
    """Exception raised when a command is used my someone that does not have access to use it
    This inherits from :exc:`CheckFailure`
    """

    def __init__(self, message=None):
        super().__init__(message or "You do not have access to use this command.")


class ArgumentParsingError(Exception):
    """This exception is raised when the parser in argparse fails to parse a command and exits."""

    def __init__(self, message=None):
        super().__init__(message or "Their is an issue in the arguments you passed in.")


class MemberNotFoundError(Exception):
    """This exception is raised when a member is not found in a server when creating officers."""

    def __init__(self, message=None):
        super().__init__(message or "The member you were searching for was not found.")


class GetRoleMembersError(Exception):
    """This exception is raised when the bot does not manage to fetch users from a role in get_role_members."""

    def __init__(self, message=None, role_name="Unknown Role"):
        super().__init__(
            message
            or f'An unknown error occurred when searching for the members in the role "{role_name}".'
        )


class MissingArgumentError(Exception):
    """This exception is raised when a command is missing an argument."""

    def __init__(self, message=None, argument_name=None):
        super().__init__(
            message
            or f"You are missing an argument{' '+ argument_name if argument_name else ''}."
        )
