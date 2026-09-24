import textwrap
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, Response, status

from timegrip.adapters.controllers.schemas import (
    EXAMPLE_UUID,
    UNAUTHORIZED_HEADERS,
    USER_NOT_FOUND_EXAMPLE,
    HTTPError,
    Page,
    ProjectAddData,
    ProjectData,
    ProjectUpdateData,
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
from timegrip.application.project.add_project import (
    AddProjectInteractor,
    AddProjectRequestDTO,
)
from timegrip.application.project.delete_project import (
    DeleteProjectInteractor,
)
from timegrip.application.project.get_all_user_projects import (
    GetAllUserProjectsInteractor,
)
from timegrip.application.project.get_project import (
    GetProjectByIdInteractor,
)
from timegrip.application.project.update_project import (
    UpdateProjectInteractor,
    UpdateProjectRequestDTO,
)

project_router = APIRouter()


@project_router.post(
    path="",
    summary="Add project",
    description=textwrap.dedent("""\
        Create a new project owned by the authenticated user. Requires a valid
        Bearer token in the `Authorization` header. The account must be
        activated.
        """),
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_color": {
                            "summary": "Unsupported color",
                            "value": {
                                "detail": "Color must be one of ...",
                                "code": "invalid_project_color",
                            },
                        },
                        "negative_hourly_rate": {
                            "summary": "Negative hourly rate",
                            "value": {
                                "detail": "Hourly rate must not be negative",
                                "code": "invalid_hourly_rate",
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
async def add_project(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[AddProjectInteractor],
    project_add_data: ProjectAddData,
) -> ProjectData:
    current_user_id = id_provider.get_id()
    add_project_dto = AddProjectRequestDTO(
        name=project_add_data.name,
        color=project_add_data.color,
        hourly_rate=project_add_data.hourly_rate,
        round_to_hour=project_add_data.round_to_hour,
        user_id=current_user_id,
    )
    project = await interactor(add_project_dto=add_project_dto)
    return ProjectData(
        id=project.id,
        name=project.name,
        color=project.color,
        hourly_rate=project.hourly_rate,
        round_to_hour=project.round_to_hour,
        status=project.status,
    )


@project_router.get(
    path="",
    summary="Get all projects",
    description=textwrap.dedent("""\
        Return a paginated list of projects owned by the authenticated user,
        ordered by creation time from oldest to newest. Use `page` and
        `page_size` to control pagination. Requires a valid Bearer token in
        the `Authorization` header. The account must be activated.

        The list includes both active and archived projects, and `total`
        counts both; use each project's `status` to tell them apart.
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
async def get_all_user_projects(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[GetAllUserProjectsInteractor],
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
) -> Page[ProjectData]:
    current_user_id = id_provider.get_id()
    result = await interactor(
        current_user_id=current_user_id,
        page=page,
        page_size=page_size,
    )
    return Page[ProjectData](
        items=[
            ProjectData(
                id=project.id,
                name=project.name,
                color=project.color,
                hourly_rate=project.hourly_rate,
                round_to_hour=project.round_to_hour,
                status=project.status,
            )
            for project in result.items
        ],
        page=page,
        page_size=page_size,
        total=result.total,
    )


@project_router.get(
    path="/{project_id}",
    summary="Get project",
    description=textwrap.dedent("""\
        Return a single project by its ID. The project must belong to the
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
                        "project_not_found": {
                            "summary": "Project not found",
                            "value": {
                                "detail": (
                                    f"Project with id {EXAMPLE_UUID} not found"
                                ),
                                "code": "project_not_found",
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
async def get_project_by_id(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[GetProjectByIdInteractor],
    project_id: UUID,
) -> ProjectData:
    current_user_id = id_provider.get_id()
    project = await interactor(
        current_user_id=current_user_id,
        project_id=project_id,
    )
    return ProjectData(
        id=project.id,
        name=project.name,
        color=project.color,
        hourly_rate=project.hourly_rate,
        round_to_hour=project.round_to_hour,
        status=project.status,
    )


@project_router.patch(
    path="/{project_id}",
    summary="Update project",
    description=textwrap.dedent("""\
        Update an existing project by its ID. The project must belong to the
        authenticated user. Requires a valid Bearer token in the
        `Authorization` header. The account must be activated.

        A project whose timer is currently running cannot be archived: stop
        the timer first.
        """),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_color": {
                            "summary": "Unsupported color",
                            "value": {
                                "detail": "Color must be one of ...",
                                "code": "invalid_project_color",
                            },
                        },
                        "invalid_status": {
                            "summary": "Unsupported status",
                            "value": {
                                "detail": "Status must be one of ...",
                                "code": "invalid_project_status",
                            },
                        },
                        "negative_hourly_rate": {
                            "summary": "Negative hourly rate",
                            "value": {
                                "detail": "Hourly rate must not be negative",
                                "code": "invalid_hourly_rate",
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
                                    f"Project with id {EXAMPLE_UUID} not found"
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
                    "example": {
                        "detail": (
                            "Cannot archive a project with a running timer"
                        ),
                        "code": "project_has_running_timer",
                    },
                },
            },
        },
    },
)
@inject
async def update_project(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[UpdateProjectInteractor],
    project_id: UUID,
    project_update_data: ProjectUpdateData,
) -> ProjectData:
    current_user_id = id_provider.get_id()
    update_project_dto = UpdateProjectRequestDTO(
        id=project_id,
        name=project_update_data.name,
        color=project_update_data.color,
        hourly_rate=project_update_data.hourly_rate,
        hourly_rate_set="hourly_rate" in project_update_data.model_fields_set,
        round_to_hour=project_update_data.round_to_hour,
        status=project_update_data.status,
    )
    project = await interactor(
        current_user_id=current_user_id,
        update_project_dto=update_project_dto,
    )
    return ProjectData(
        id=project.id,
        name=project.name,
        color=project.color,
        hourly_rate=project.hourly_rate,
        round_to_hour=project.round_to_hour,
        status=project.status,
    )


@project_router.delete(
    path="/{project_id}",
    summary="Delete project",
    description=textwrap.dedent("""\
        Delete a project by its ID. The project must belong to the
        authenticated user. Returns no content on success. Requires a valid
        Bearer token in the `Authorization` header. The account must be
        activated.

        Deleting a project permanently deletes all of its time entries as
        well. A project whose timer is currently running cannot be deleted:
        stop the timer first. To hide a project without losing its history,
        archive it instead via `PATCH /api/projects/{project_id}`.
        """),
    status_code=status.HTTP_204_NO_CONTENT,
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
                                    f"Project with id {EXAMPLE_UUID} not found"
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
                    "example": {
                        "detail": (
                            "Cannot delete a project with a running timer"
                        ),
                        "code": "project_has_running_timer",
                    },
                },
            },
        },
    },
)
@inject
async def delete_project(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[DeleteProjectInteractor],
    project_id: UUID,
) -> Response:
    current_user_id = id_provider.get_id()
    await interactor(current_user_id=current_user_id, project_id=project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
