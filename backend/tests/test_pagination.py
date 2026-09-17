import pytest

from timegrip.application.common.pagination import (
    MAX_PAGE,
    Pagination,
    paginate,
)


@pytest.mark.parametrize(
    ("page", "page_size", "expected"),
    [
        (1, 10, Pagination(offset=0, limit=10)),
        (3, 10, Pagination(offset=20, limit=10)),
    ],
)
def test_paginate_computes_offset(page, page_size, expected):
    assert paginate(page=page, page_size=page_size) == expected


@pytest.mark.parametrize("page", [0, -1])
def test_paginate_invalid_page(page):
    with pytest.raises(ValueError, match="Page must be >= 1"):
        paginate(page=page, page_size=10)


def test_paginate_accepts_max_page():
    result = paginate(page=MAX_PAGE, page_size=100)
    assert result == Pagination(offset=(MAX_PAGE - 1) * 100, limit=100)


def test_paginate_page_above_max():
    with pytest.raises(ValueError, match="Page must be <="):
        paginate(page=MAX_PAGE + 1, page_size=10)


@pytest.mark.parametrize("page_size", [1, 100])
def test_paginate_accepts_page_size_bounds(page_size):
    result = paginate(page=2, page_size=page_size)
    assert result == Pagination(offset=page_size, limit=page_size)


@pytest.mark.parametrize("page_size", [0, 101])
def test_paginate_invalid_page_size(page_size):
    with pytest.raises(ValueError, match="Page size must be between"):
        paginate(page=1, page_size=page_size)
