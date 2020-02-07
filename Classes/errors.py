from discord.ext import commands

class NotReadyYet(commands.CheckFailure):
    """Exception raised when the bot is not ready yet.
    This inherits from :exc:`CheckFailure`
    """
    def __init__(self, message=None):
        super().__init__(message or 'I am still starting up, give me a moment.')
