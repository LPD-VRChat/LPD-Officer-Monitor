import os
from unittest.mock import Mock

import pytest


@pytest.fixture(autouse=True)
def replace_role_ladder(monkeypatch: pytest.MonkeyPatch):
    """
    Replace the settings with a fake one for the duration of the tests in this
    file.

    This makes sure that your settings configuration has no effect on the
    result of these tests unless you modify base.py.
    """
    os.environ["LPD_OFFICER_MONITOR_UNIT_TESTING"] = "TRUE"


def test_is_lpd_member_officer(member: Mock):
    from src.layers.business.extra_functions import is_lpd_member

    member.roles[0].id = 834215801426018335
    assert is_lpd_member(member) == True


def test_is_lpd_member_chief(member: Mock):
    from src.layers.business.extra_functions import is_lpd_member

    member.roles[1].id = 645388308158873610
    assert is_lpd_member(member) == True


def test_is_lpd_member_no_roles(member: Mock):
    from src.layers.business.extra_functions import is_lpd_member

    member.roles = []
    assert is_lpd_member(member) == False


def test_is_lpd_member_other_roles(member: Mock):
    from src.layers.business.extra_functions import is_lpd_member

    assert is_lpd_member(member) == False
