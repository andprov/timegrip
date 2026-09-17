from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from timegrip.adapters.controllers.schemas import (
    ProjectAddData,
    ProjectUpdateData,
    TimerBulkDeleteData,
    TimerManualAddData,
    TimerUpdateData,
    UserAddData,
)

TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")


@pytest.mark.parametrize("schema", [ProjectAddData, ProjectUpdateData])
def test_project_data_accepts_max_hourly_rate(schema):
    data = schema(name="Website Redesign", hourly_rate=Decimal("99999999.99"))
    assert data.hourly_rate == Decimal("99999999.99")


@pytest.mark.parametrize("schema", [ProjectAddData, ProjectUpdateData])
@pytest.mark.parametrize(
    "hourly_rate",
    [Decimal("123456789"), Decimal("50.001")],
    ids=["too_many_digits", "too_many_decimals"],
)
def test_project_data_rejects_hourly_rate_out_of_precision(
    schema,
    hourly_rate,
):
    with pytest.raises(ValidationError):
        schema(name="Website Redesign", hourly_rate=hourly_rate)


def test_project_update_data_distinguishes_null_from_omitted_hourly_rate():
    omitted = ProjectUpdateData.model_validate({"name": "New name"})
    cleared = ProjectUpdateData.model_validate({"hourly_rate": None})
    assert "hourly_rate" not in omitted.model_fields_set
    assert "hourly_rate" in cleared.model_fields_set
    assert cleared.hourly_rate is None


def test_timer_manual_add_data_rejects_naive_datetimes():
    with pytest.raises(ValidationError):
        TimerManualAddData(
            project_id=TEST_PROJECT_ID,
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
        )


def test_timer_update_data_rejects_naive_datetime():
    with pytest.raises(ValidationError):
        TimerUpdateData.model_validate({"start_time": "2024-01-01T10:00:00"})


def test_timer_bulk_delete_data_requires_at_least_one_id():
    with pytest.raises(ValidationError):
        TimerBulkDeleteData(ids=[])


@pytest.mark.parametrize("email", ["not-an-email", "user@", "@example.com"])
def test_user_add_data_rejects_invalid_email(email):
    with pytest.raises(ValidationError):
        UserAddData(email=email, password="Passw0rd")
