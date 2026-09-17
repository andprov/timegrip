from dataclasses import dataclass

PAGE = 1
MAX_PAGE = 1_000_000
PAGE_SIZE = 10
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class Pagination:
    offset: int
    limit: int


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total: int


def paginate(page: int, page_size: int) -> Pagination:
    if page < 1:
        raise ValueError("Page must be >= 1")

    if page > MAX_PAGE:
        raise ValueError(f"Page must be <= {MAX_PAGE}")

    if page_size < MIN_PAGE_SIZE or page_size > MAX_PAGE_SIZE:
        raise ValueError(
            f"Page size must be between {MIN_PAGE_SIZE} and {MAX_PAGE_SIZE}",
        )

    offset = (page - 1) * page_size
    return Pagination(offset=offset, limit=page_size)
