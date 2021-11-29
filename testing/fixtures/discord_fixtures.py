from unittest.mock import MagicMock, Mock

import discord
import pytest


@pytest.fixture(scope="session")
def role_1():
    fake_role = MagicMock(discord.Role)
    fake_role.id = 593468946523679856
    return fake_role


@pytest.fixture(scope="session")
def role_2():
    fake_role = MagicMock(discord.Role)
    fake_role.id = 643258953251357092
    return fake_role


@pytest.fixture(scope="session")
def member(role_1, role_2):
    fake_member = MagicMock(discord.Member)
    fake_member.id = 378666988412731404
    fake_member.mention = f"<@{fake_member.id}>"
    fake_member.name = "Hroi"
    fake_member.display_name = fake_member.name
    fake_member.discriminator = "1994"
    fake_member.bot = False

    fake_member.roles = [role_1, role_2]
    return fake_member
