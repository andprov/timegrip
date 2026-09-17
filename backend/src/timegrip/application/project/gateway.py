from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from timegrip.entities.project import Project


class ProjectGateway(Protocol):
    @abstractmethod
    async def add_project(self, project: Project) -> Project:
        raise NotImplementedError

    @abstractmethod
    async def get_all_user_projects(
        self,
        user_id: UUID,
        offset: int,
        limit: int,
    ) -> list[Project]:
        raise NotImplementedError

    @abstractmethod
    async def count_user_projects(self, user_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_project_by_id(self, id: UUID) -> Project | None:
        raise NotImplementedError

    @abstractmethod
    async def update_project(self, project: Project) -> Project:
        raise NotImplementedError

    @abstractmethod
    async def delete_project(self, id: UUID) -> None:
        raise NotImplementedError
