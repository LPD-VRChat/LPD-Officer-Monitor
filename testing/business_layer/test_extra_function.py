import os
from unittest.mock import Mock

import pytest

from src.layers.business.extra_functions import is_lpd_member


def test_is_lpd_member_officer(member: Mock):
    member.roles[0].id = 834215801426018335
    assert is_lpd_member(member) == True


def test_is_lpd_member_chief(member: Mock):
    member.roles[1].id = 645388308158873610
    assert is_lpd_member(member) == True


def test_is_lpd_member_no_roles(member: Mock):
    member.roles = []
    assert is_lpd_member(member) == False


def test_is_lpd_member_other_roles(member: Mock):
    assert is_lpd_member(member) == False
