import textwrap
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, Response, status
from pydantic import AwareDatetime

from timegrip.adapters.controllers.schemas import (
    EXAMPLE_UUID,
    TZ_DESCRIPTION,
    UNAUTHORIZED_HEADERS,
    USER_NOT_FOUND_EXAMPLE,
    HTTPError,
    Page,
    TimerBulkDeleteData,
    TimerData,
    TimerManualAddData,
    TimerRunningData,
    TimerStartData,
    TimerUpdateData,
)
from timegrip.application.common.id_provider_gateway import (
    IdProviderGateway,
)
from timegrip.application.common.pagination import (
    MAX_PAGE,
    MAX_PAGE_SIZE,
    MIN_PAGE_SIZE,
    PAGE,
    PAGE_SIZE,
)
from timegrip.application.timer.add_manual_timer import (
    AddManualTimerInteractor,
    AddManualTimerRequestDTO,
)
from timegrip.application.timer.bulk_delete_timer import (
    BulkDeleteTimerInteractor,
)
from timegrip.application.timer.delete_timer import (
    DeleteTimerInteractor,
)
from timegrip.application.timer.get_all_user_timers import (
    GetAllUserTimersInteractor,
)
from timegrip.application.timer.get_running_timer import (
    GetRunningTimerInteractor,
)
from timegrip.application.timer.get_timer import GetTimerByIdInteractor
from timegrip.application.timer.start_timer import (
    StartTimerInteractor,
    StartTimerRequestDTO,
)
from timegrip.application.timer.stop_timer import StopTimerInteractor
from timegrip.application.timer.update_timer import (
    UpdateTimerInteractor,
    UpdateTimerRequestDTO,
)
from timegrip.entities.timer import MIN_TIMER_START

timer_router = APIRouter()


@timer_router.post(
    path="",
    summary="Add manual timer entry",
    description=textwrap.dedent(f"""\
        Create a time entry with an explicit start and end time, for
        backdating work that wasn't tracked live. Neither time may be in the
        future, and the start time must not be before
        {MIN_TIMER_START:%Y-%m-%d}. The project must belong to the
        authenticated user and must not be archived, and the entry must not
        overlap with an existing one — including a currently running timer.
        To track time live, use
        `POST /api/timers/start` instead. Requires a valid Bearer token in
        the `Authorization` header. The account must be activated.
        """),
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_range": {
                            "summary": "Invalid time range",
                            "value": {
                                "detail": "End time must be after start time",
                                "code": "end_time_before_start",
                            },
                        },
                        "start_time_in_future": {
                            "summary": "Start time in the future",
                            "value": {
                                "detail": (
                                    "Start time must not be in the future"
                                ),
                                "code": "start_time_in_future",
                            },
                        },
                        "end_time_in_future": {
                            "summary": "End time in the future",
                            "value": {
                                "detail": (
                                    "End time must not be in the future"
                                ),
                                "code": "end_time_in_future",
                            },
                        },
                        "too_early": {
                            "summary": "Start time too early",
                            "value": {
                                "detail": (
                                    f"Start time must not be before "
                                    f"{MIN_TIMER_START:%Y-%m-%d}"
                                ),
                                "code": "start_time_too_early",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied",
                        "code": "access_denied",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "project_not_found": {
                            "summary": "Project not found",
                            "value": {
                                "detail": (
                                    f"Project with id {EXAMPLE_UUID} not "
                                    f"found"
                                ),
                                "code": "project_not_found",
                            },
                        },
                        "user_not_found": USER_NOT_FOUND_EXAMPLE,
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "overlap": {
                            "summary": "Overlapping entry",
                            "value": {
                                "detail": (
                                    "Timer overlaps with an existing time "
                                    "entry"
                                ),
                                "code": "timer_overlap",
                            },
                        },
                        "archived_project": {
                            "summary": "Archived project",
                            "value": {
                                "detail": (
                                    "Cannot add a time entry for an "
                                    "archived project"
                                ),
                                "code": "project_archived",
                            },
                        },
                    },
                },
            },
        },
    },
)
@inject
async def add_manual_timer(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[AddManualTimerInteractor],
    timer_manual_add_data: TimerManualAddData,
) -> TimerData:
    current_user_id = id_provider.get_id()
    add_timer_dto = AddManualTimerRequestDTO(
        project_id=timer_manual_add_data.project_id,
        user_id=current_user_id,
        start_time=timer_manual_add_data.start_time,
        end_time=timer_manual_add_data.end_time,
    )
    timer = await interactor(add_timer_dto=add_timer_dto)
    return TimerData(
        id=timer.id,
        start_time=timer.start_time,
        end_time=timer.end_time,
        duration=timer.duration,
        hourly_rate=timer.hourly_rate,
        round_to_hour=timer.round_to_hour,
        billable_amount=timer.billable_amount,
        user_id=timer.user_id,
        project_id=timer.project_id,
    )


@timer_router.post(
    path="/start",
    summary="Start timer",
    description=textwrap.dedent("""\
        Start a new timer for the given project. The project must belong to the
        authenticated user and must not be archived, and the user must not
        already have a running timer. Requires a valid Bearer token in the
        `Authorization` header. The account must be activated.
        """),
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied",
                        "code": "access_denied",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "project_not_found": {
                            "summary": "Project not found",
                            "value": {
                                "detail": (
                                    f"Project with id {EXAMPLE_UUID} not "
                                    f"found"
                                ),
                                "code": "project_not_found",
                            },
                        },
                        "user_not_found": USER_NOT_FOUND_EXAMPLE,
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "already_running": {
                            "summary": "Timer already running",
                            "value": {
                                "detail": "A timer is already running",
                                "code": "timer_already_running",
                            },
                        },
                        "archived_project": {
                            "summary": "Archived project",
                            "value": {
                                "detail": (
                                    "Cannot start a timer for an archived "
                                    "project"
                                ),
                                "code": "project_archived",
                            },
                        },
                    },
                },
            },
        },
    },
)
@inject
async def start_timer(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[StartTimerInteractor],
    timer_start_data: TimerStartData,
) -> TimerRunningData:
    current_user_id = id_provider.get_id()
    start_timer_dto = StartTimerRequestDTO(
        project_id=timer_start_data.project_id,
        user_id=current_user_id,
    )
    timer = await interactor(start_timer_dto=start_timer_dto)
    return TimerRunningData(
        id=timer.id,
        start_time=timer.start_time,
        hourly_rate=timer.hourly_rate,
        round_to_hour=timer.round_to_hour,
        user_id=timer.user_id,
        project_id=timer.project_id,
    )


@timer_router.post(
    path="/stop",
    summary="Stop timer",
    description=textwrap.dedent("""\
        Stop the currently running timer for the authenticated user. Requires a
        valid Bearer token in the `Authorization` header. The account must be
        activated.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied",
                        "code": "access_denied",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No running timer",
                        "code": "timer_not_running",
                    },
                },
            },
        },
    },
)
@inject
async def stop_timer(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[StopTimerInteractor],
) -> TimerData:
    current_user_id = id_provider.get_id()
    timer = await interactor(current_user_id=current_user_id)
    return TimerData(
        id=timer.id,
        start_time=timer.start_time,
        end_time=timer.end_time,
        duration=timer.duration,
        hourly_rate=timer.hourly_rate,
        round_to_hour=timer.round_to_hour,
        billable_amount=timer.billable_amount,
        user_id=timer.user_id,
        project_id=timer.project_id,
    )


@timer_router.get(
    path="/running",
    summary="Get currently running timer",
    description=textwrap.dedent("""\
        Return the currently running timer for the authenticated user, or
        `null` if no timer is running. Requires a valid Bearer token in the
        `Authorization` header. The account must be activated.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied",
                        "code": "access_denied",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
    },
)
@inject
async def get_running_timer(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[GetRunningTimerInteractor],
) -> TimerRunningData | None:
    current_user_id = id_provider.get_id()
    timer = await interactor(current_user_id=current_user_id)
    if timer is None:
        return None

    return TimerRunningData(
        id=timer.id,
        start_time=timer.start_time,
        hourly_rate=timer.hourly_rate,
        round_to_hour=timer.round_to_hour,
        user_id=timer.user_id,
        project_id=timer.project_id,
    )


@timer_router.get(
    path="",
    summary="Get all timers",
    description=textwrap.dedent("""\
        Return a paginated list of timers owned by the authenticated user,
        ordered by start time from most to least recent. Use `page` and
        `page_size` to control pagination, and `project_id`, `date_from`,
        `date_to`, `billable`, and `include_archived_projects` to filter the
        results. Requires a valid Bearer token in the `Authorization` header.
        The account must be activated.

        The list includes the currently running timer, if there is one and
        it matches the filters. Its `end_time`, `duration`, and
        `billable_amount` are `null`.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied",
                        "code": "access_denied",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
    },
)
@inject
async def get_all_user_timers(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[GetAllUserTimersInteractor],
    page: int = Query(
        PAGE,
        ge=PAGE,
        le=MAX_PAGE,
        description=(
            f"1-indexed page number, from {PAGE} to {MAX_PAGE}. Defaults to "
            f"{PAGE}."
        ),
    ),
    page_size: int = Query(
        PAGE_SIZE,
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
        description=(
            f"Number of items per page, from {MIN_PAGE_SIZE} to "
            f"{MAX_PAGE_SIZE}. Defaults to {PAGE_SIZE}."
        ),
    ),
    project_id: list[UUID] | None = Query(
        None,
        description="Only return timers for these projects. Repeat the "
        "parameter to filter by multiple projects.",
    ),
    date_from: AwareDatetime | None = Query(
        None,
        description=f"Only return timers starting on or after this time. "
        f"{TZ_DESCRIPTION}",
    ),
    date_to: AwareDatetime | None = Query(
        None,
        description=f"Only return timers starting on or before this time. "
        f"{TZ_DESCRIPTION}",
    ),
    billable: bool | None = Query(
        None,
        description=(
            "Filter by whether the timer has an hourly rate: `true` for "
            "billable timers, `false` for non-billable ones. Matches on "
            "the rate stored on the timer, not the project's current "
            "rate, so entries created while the project was billable stay "
            "billable after its rate is cleared."
        ),
    ),
    include_archived_projects: bool = Query(
        False,
        description=(
            "Include timers whose project has been archived. Defaults to "
            "`false`, which only returns timers for active projects."
        ),
    ),
) -> Page[TimerData]:
    current_user_id = id_provider.get_id()
    result = await interactor(
        current_user_id=current_user_id,
        page=page,
        page_size=page_size,
        project_ids=project_id,
        date_from=date_from,
        date_to=date_to,
        billable=billable,
        include_archived_projects=include_archived_projects,
    )
    return Page[TimerData](
        items=[
            TimerData(
                id=timer.id,
                start_time=timer.start_time,
                end_time=timer.end_time,
                duration=timer.duration,
                hourly_rate=timer.hourly_rate,
                round_to_hour=timer.round_to_hour,
                billable_amount=timer.billable_amount,
                user_id=timer.user_id,
                project_id=timer.project_id,
            )
            for timer in result.items
        ],
        page=page,
        page_size=page_size,
        total=result.total,
    )


@timer_router.get(
    path="/{timer_id}",
    summary="Get timer",
    description=textwrap.dedent("""\
        Return a single timer by its ID. The timer must belong to the
        authenticated user. Requires a valid Bearer token in the
        `Authorization` header. The account must be activated.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied",
                        "code": "access_denied",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "timer_not_found": {
                            "summary": "Timer not found",
                            "value": {
                                "detail": (
                                    f"Timer with id {EXAMPLE_UUID} not found"
                                ),
                                "code": "timer_not_found",
                            },
                        },
                        "user_not_found": USER_NOT_FOUND_EXAMPLE,
                    },
                },
            },
        },
    },
)
@inject
async def get_timer_by_id(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[GetTimerByIdInteractor],
    timer_id: UUID,
) -> TimerData:
    current_user_id = id_provider.get_id()
    timer = await interactor(
        current_user_id=current_user_id,
        timer_id=timer_id,
    )
    return TimerData(
        id=timer.id,
        start_time=timer.start_time,
        end_time=timer.end_time,
        duration=timer.duration,
        hourly_rate=timer.hourly_rate,
        round_to_hour=timer.round_to_hour,
        billable_amount=timer.billable_amount,
        user_id=timer.user_id,
        project_id=timer.project_id,
    )


@timer_router.patch(
    path="/{timer_id}",
    summary="Update timer",
    description=textwrap.dedent(f"""\
        Update an existing, already stopped timer by its ID: reassign its
        project or adjust its start/end time. The timer must belong to the
        authenticated user and must not be currently running, neither time
        may be in the future, the start time must not be before
        {MIN_TIMER_START:%Y-%m-%d}, the new project must not be archived,
        and the updated range must not overlap with an existing entry.
        Requires a valid Bearer token in the `Authorization` header. The
        account must be activated.

        Reassigning the entry to another project re-reads `hourly_rate`
        and `round_to_hour` from that project and recomputes
        `billable_amount` with them. Editing only the times recomputes
        `billable_amount` from the rate already stored on the entry, which
        may differ from the project's current rate. Sending the project's
        current `project_id` does not refresh the stored rate.
        """),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_range": {
                            "summary": "Invalid time range",
                            "value": {
                                "detail": "End time must be after start time",
                                "code": "end_time_before_start",
                            },
                        },
                        "start_time_in_future": {
                            "summary": "Start time in the future",
                            "value": {
                                "detail": (
                                    "Start time must not be in the future"
                                ),
                                "code": "start_time_in_future",
                            },
                        },
                        "end_time_in_future": {
                            "summary": "End time in the future",
                            "value": {
                                "detail": (
                                    "End time must not be in the future"
                                ),
                                "code": "end_time_in_future",
                            },
                        },
                        "too_early": {
                            "summary": "Start time too early",
                            "value": {
                                "detail": (
                                    f"Start time must not be before "
                                    f"{MIN_TIMER_START:%Y-%m-%d}"
                                ),
                                "code": "start_time_too_early",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied",
                        "code": "access_denied",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "timer_not_found": {
                            "summary": "Timer not found",
                            "value": {
                                "detail": (
                                    f"Timer with id {EXAMPLE_UUID} not found"
                                ),
                                "code": "timer_not_found",
                            },
                        },
                        "project_not_found": {
                            "summary": "Reassigned project not found",
                            "value": {
                                "detail": (
                                    f"Project with id {EXAMPLE_UUID} not "
                                    f"found"
                                ),
                                "code": "project_not_found",
                            },
                        },
                        "user_not_found": USER_NOT_FOUND_EXAMPLE,
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "timer_running": {
                            "summary": "Timer still running",
                            "value": {
                                "detail": (
                                    "Timer is running, stop it before editing"
                                ),
                                "code": "timer_running",
                            },
                        },
                        "overlap": {
                            "summary": "Overlapping entry",
                            "value": {
                                "detail": (
                                    "Timer overlaps with an existing time "
                                    "entry"
                                ),
                                "code": "timer_overlap",
                            },
                        },
                        "archived_project": {
                            "summary": "Archived project",
                            "value": {
                                "detail": (
                                    "Cannot reassign a time entry to an "
                                    "archived project"
                                ),
                                "code": "project_archived",
                            },
                        },
                    },
                },
            },
        },
    },
)
@inject
async def update_timer(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[UpdateTimerInteractor],
    timer_id: UUID,
    timer_update_data: TimerUpdateData,
) -> TimerData:
    current_user_id = id_provider.get_id()
    update_timer_dto = UpdateTimerRequestDTO(
        id=timer_id,
        project_id=timer_update_data.project_id,
        start_time=timer_update_data.start_time,
        end_time=timer_update_data.end_time,
    )
    timer = await interactor(
        current_user_id=current_user_id,
        update_timer_dto=update_timer_dto,
    )
    return TimerData(
        id=timer.id,
        start_time=timer.start_time,
        end_time=timer.end_time,
        duration=timer.duration,
        hourly_rate=timer.hourly_rate,
        round_to_hour=timer.round_to_hour,
        billable_amount=timer.billable_amount,
        user_id=timer.user_id,
        project_id=timer.project_id,
    )


@timer_router.delete(
    path="",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete multiple timers",
    description=textwrap.dedent("""\
        Delete multiple timers by their IDs in a single request. All timers
        must belong to the authenticated user, and none of them may be
        currently running: stop the timer first. If any timer fails these
        checks, nothing is deleted. Returns no content on success. Requires a
        valid Bearer token in the `Authorization` header. The account must be
        activated.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied",
                        "code": "access_denied",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "timer_not_found": {
                            "summary": "Timer not found",
                            "value": {
                                "detail": (
                                    f"Timer with id {EXAMPLE_UUID} not found"
                                ),
                                "code": "timer_not_found",
                            },
                        },
                        "user_not_found": USER_NOT_FOUND_EXAMPLE,
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Timer is running, stop it before deleting",
                        "code": "timer_running",
                    },
                },
            },
        },
    },
)
@inject
async def bulk_delete_timers(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[BulkDeleteTimerInteractor],
    timer_bulk_delete_data: TimerBulkDeleteData,
) -> Response:
    current_user_id = id_provider.get_id()
    await interactor(
        current_user_id=current_user_id,
        timer_ids=timer_bulk_delete_data.ids,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@timer_router.delete(
    path="/{timer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete timer",
    description=textwrap.dedent("""\
        Delete a timer by its ID. The timer must belong to the authenticated
        user and must not be currently running: stop the timer first. Returns
        no content on success. Requires a valid Bearer token in the
        `Authorization` header. The account must be activated.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied",
                        "code": "access_denied",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "timer_not_found": {
                            "summary": "Timer not found",
                            "value": {
                                "detail": (
                                    f"Timer with id {EXAMPLE_UUID} not found"
                                ),
                                "code": "timer_not_found",
                            },
                        },
                        "user_not_found": USER_NOT_FOUND_EXAMPLE,
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Timer is running, stop it before deleting",
                        "code": "timer_running",
                    },
                },
            },
        },
    },
)
@inject
async def delete_timer(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[DeleteTimerInteractor],
    timer_id: UUID,
) -> Response:
    current_user_id = id_provider.get_id()
    await interactor(current_user_id=current_user_id, timer_id=timer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
