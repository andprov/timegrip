from decimal import Decimal
from uuid import UUID

import pytest

from timegrip.entities.exceptions import InvalidHourlyRateError
from timegrip.entities.project import Project, ProjectColor, ProjectStatus

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_project(**overrides):
    defaults = {
        "id": None,
        "name": "Website Redesign",
        "color": ProjectColor.GRAY,
        "hourly_rate": None,
        "round_to_hour": False,
        "status": ProjectStatus.ACTIVE,
        "user_id": TEST_USER_ID,
        "created_at": None,
    }
    defaults.update(overrides)
    return Project(**defaults)


def test_project_rejects_negative_hourly_rate():
    with pytest.raises(InvalidHourlyRateError) as exc_info:
        _make_project(hourly_rate=Decimal("-0.01"))
    assert exc_info.value.code == "invalid_hourly_rate"
    assert str(exc_info.value) == "Hourly rate must not be negative"


def test_project_stores_zero_hourly_rate_as_none():
    project = _make_project(hourly_rate=Decimal("0"), round_to_hour=True)
    assert project.hourly_rate is None
    assert project.round_to_hour is False


def test_project_without_hourly_rate_resets_round_to_hour():
    project = _make_project(hourly_rate=None, round_to_hour=True)
    assert project.hourly_rate is None
    assert project.round_to_hour is False


def test_project_keeps_round_to_hour_with_hourly_rate():
    project = _make_project(hourly_rate=Decimal("50.00"), round_to_hour=True)
    assert project.hourly_rate == Decimal("50.00")
    assert project.round_to_hour is True
