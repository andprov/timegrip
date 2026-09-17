from uuid import UUID

import pytest

from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_user(email):
    return User(
        id=TEST_USER_ID,
        email=email,
        hashed_password="hash",
        is_active=True,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )


def test_email_lowercases_whole_address():
    email = Email("John.Doe@Example.COM")
    assert email.value == "john.doe@example.com"
    assert str(email) == "john.doe@example.com"


def test_user_rejects_raw_string_email():
    with pytest.raises(TypeError, match="must be an Email"):
        _make_user(email="john.doe@example.com")
