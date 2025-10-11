import pytest
from importlib import reload
import os


def test_settings_module():
    import settings


def test_settings_profiles():
    import settings

    assert settings.CONFIG_LOADED == "base_test"


def test_settings_role_ladder():
    import settings

    assert settings.ROLE_LADDER.cadet < settings.ROLE_LADDER.recruit
    assert settings.ROLE_LADDER.recruit < settings.ROLE_LADDER.officer
    assert settings.ROLE_LADDER.officer < settings.ROLE_LADDER.senior_officer
    assert settings.ROLE_LADDER.senior_officer < settings.ROLE_LADDER.corporal
    assert settings.ROLE_LADDER.corporal < settings.ROLE_LADDER.sergeant
    assert settings.ROLE_LADDER.sergeant < settings.ROLE_LADDER.staff_sergeant
    assert settings.ROLE_LADDER.staff_sergeant < settings.ROLE_LADDER.advisor
    assert settings.ROLE_LADDER.advisor < settings.ROLE_LADDER.lieutenant
    assert settings.ROLE_LADDER.lieutenant < settings.ROLE_LADDER.captain
    assert settings.ROLE_LADDER.captain < settings.ROLE_LADDER.deputy_chief
    assert settings.ROLE_LADDER.deputy_chief < settings.ROLE_LADDER.chief
