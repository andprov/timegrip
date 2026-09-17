import logging
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from timegrip.adapters.db.db_tables import ProjectDBModel
from timegrip.application.exceptions import ProjectNotFoundError
from timegrip.application.project.gateway import ProjectGateway
from timegrip.entities.project import Project, ProjectColor, ProjectStatus

logger = logging.getLogger(__name__)


class DatabaseProjectGateway(ProjectGateway):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_project(self, project: Project) -> Project:
        new_project = ProjectDBModel(
            name=project.name,
            color=project.color,
            hourly_rate=project.hourly_rate,
            round_to_hour=project.round_to_hour,
            status=project.status,
            user_id=project.user_id,
        )
        self.session.add(new_project)
        await self.session.flush()
        await self.session.refresh(new_project)
        added_project = Project(
            id=new_project.id,
            name=new_project.name,
            color=ProjectColor(new_project.color),
            hourly_rate=new_project.hourly_rate,
            round_to_hour=new_project.round_to_hour,
            status=ProjectStatus(new_project.status),
            user_id=new_project.user_id,
            created_at=new_project.created_at,
        )
        await self.session.commit()
        logger.info(f"Add project | [id: {added_project.id}]")
        return added_project

    async def get_all_user_projects(
        self,
        user_id: UUID,
        offset: int,
        limit: int,
    ) -> list[Project]:
        stmt = (
            select(ProjectDBModel)
            .where(ProjectDBModel.user_id == user_id)
            .order_by(ProjectDBModel.created_at)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        projects = result.all()
        logger.info(
            f"Get all projects | "
            f"[count: {len(projects)}, offset: {offset}, page_size: {limit}]",
        )
        return [
            Project(
                id=project.id,
                name=project.name,
                color=ProjectColor(project.color),
                hourly_rate=project.hourly_rate,
                round_to_hour=project.round_to_hour,
                status=ProjectStatus(project.status),
                user_id=project.user_id,
                created_at=project.created_at,
            )
            for project in projects
        ]

    async def count_user_projects(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(ProjectDBModel)
            .where(ProjectDBModel.user_id == user_id)
        )
        total = await self.session.scalar(stmt)
        logger.info(f"Count projects | [user_id: {user_id}, total: {total}]")
        return total or 0

    async def get_project_by_id(self, id: UUID) -> Project | None:
        project = await self.session.get(entity=ProjectDBModel, ident=id)
        if project is None:
            logger.info(f"Get project by id | [id: {id} Not Found]")
            return None

        logger.info(f"Get project by id | [project: {project}]")
        return Project(
            id=project.id,
            name=project.name,
            color=ProjectColor(project.color),
            hourly_rate=project.hourly_rate,
            round_to_hour=project.round_to_hour,
            status=ProjectStatus(project.status),
            user_id=project.user_id,
            created_at=project.created_at,
        )

    async def update_project(self, project: Project) -> Project:
        stmt = (
            update(ProjectDBModel)
            .where(ProjectDBModel.id == project.id)
            .values(
                name=project.name,
                color=project.color,
                hourly_rate=project.hourly_rate,
                round_to_hour=project.round_to_hour,
                status=project.status,
            )
            .returning(ProjectDBModel)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        try:
            updated_project = result.scalar_one()
        except NoResultFound:
            logger.warning(
                f"Update project | [id: {project.id} Not Found]",
            )
            raise ProjectNotFoundError(
                f"Project with id {project.id} not found",
            ) from None

        logger.info(f"Update project | [project_id: {updated_project.id}]")
        return Project(
            id=updated_project.id,
            name=updated_project.name,
            color=ProjectColor(updated_project.color),
            hourly_rate=updated_project.hourly_rate,
            round_to_hour=updated_project.round_to_hour,
            status=ProjectStatus(updated_project.status),
            user_id=updated_project.user_id,
            created_at=updated_project.created_at,
        )

    async def delete_project(self, id: UUID) -> None:
        stmt = delete(ProjectDBModel).filter_by(id=id)
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Delete project | [project_id: {id}]")
