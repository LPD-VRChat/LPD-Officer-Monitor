import os
import inspect
from posix import times_result
import BusinessLayer.checks as checks


def prompt(question, p="> "):
    print(question)
    response = input(p)
    if response == "":
        return prompt()
    if response == "exit":
        os._exit(0)
    return response


print("OK, so you want to create a new class of DiscordCommands.")
print("Remember to use valid Python names at all prompts!")
print(
    "(If you're not sure what to do, just type 'exit' at any time to abort without saving.)"
)
print("")
className = prompt("What should the Category name be?")
className = className.capitalize()

colorName = prompt(
    "What should the color be? Remember to use a valid discord.Color name.",
    "discord.Color.",
)
colorName = colorName.lower()
if "()" not in colorName:
    colorName = colorName + "()"

addCommands = prompt("Would you like to start adding commands?", "y/n > ")
if addCommands.lower() != "yes" and addCommands.lower() != "y":
    addCommands = False
else:
    print("")
    print(f"OK, so you want to add commands to class {className}.")
    print("Remember to use valid Python names at all prompts!")
    print(
        "(If you're not sure what to do, just type 'exit' at any time to abort without saving.)"
    )
    print("")
    commands = []
    available_checks = [x[0] for x in inspect.getmembers(checks, inspect.isfunction)]
    while True:
        command = prompt("What should the command name be?")
        command_checks = []
        while True:
            print(available_checks)
            check = prompt(
                "What checks from the list above would you like to use? ('n' for none)"
            )
            if check.lower() == "none" or check.lower() == "n":
                break
            elif check not in available_checks:
                print("That's not a valid check!")
                continue
            command_checks.append(check)
            moreChecks = prompt("Would you like to add more checks?", "y/n > ")
            if moreChecks.lower() == "no" or moreChecks.lower() == "n":
                break
        commands.append((command, command_checks))
        moreCommands = prompt("Would you like to add another command?", "y/n > ")
        if moreCommands.lower() == "no" or moreCommands.lower() == "n":
            break

print("Generating the code now...")

outputCode = f"""# Settings import
import Settings

# Standard
import traceback
import asyncio
import argparse

# Community
import discord
from discord.ext import commands

# Custom
from BusinessLayer.extra_functions import handle_error
from BusinessLayer.extra_functions import ts_print as print
import BusinessLayer.checks as checks

class {className}(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.{colorName}
    
    """

newline = f"\n"
if addCommands:
    for command in commands:
        check_block = ""
        if command[1] != []:
            for check in command[1]:
                check_block += f"""
    @checks.{check}()"""

        outputCode += f'''{check_block}
    @commands.command()
    async def {command[0]}(self, ctx):
        """{command[0]} description"""
        pass
        
        '''

outputCode += f"""
def setup(bot):
    bot.add_cog({className}(bot))
"""

thisDir = os.listdir()
if "UILayer" in thisDir:
    os.chdir("UILayer")
    thisDir = os.listdir()
    if "DiscordCommands" in thisDir:
        os.chdir("DiscordCommands")
        thisDir = os.listdir()
        if f"{className}.py" in thisDir:
            print("This class already exists!")
        else:
            with open(f"{className}.py", "w") as f:
                f.write(outputCode)
            print("Done!")
            os._exit(0)
saved = False
while not saved:
    print()
    print(os.getcwd())
    print(os.listdir())
    print("Pick a save folder - press enter to save in this directory")
    path = input(os.getcwd() + "/")
    if path == "":
        with open(f"{className}.py", "w") as f:
            f.write(outputCode)
        print("Done!")
        saved = True
    else:
        if path[-1] == "/":
            path = path[:-1]
        try:
            os.chdir(path)
        except FileNotFoundError:
            print("That folder doesn't exist!")
