import { apiFetch } from '@/api/client'
import type { Page, Project, ProjectAddData, ProjectUpdateData } from '@/api/types'

export function listProjects(
  page: number,
  pageSize: number,
): Promise<Page<Project>> {
  return apiFetch<Page<Project>>('/projects', {
    query: { page, page_size: pageSize },
  })
}

export function getProject(id: string): Promise<Project> {
  return apiFetch<Project>(`/projects/${id}`)
}

export function createProject(data: ProjectAddData): Promise<Project> {
  return apiFetch<Project>('/projects', { method: 'POST', body: data })
}

export function updateProject(
  id: string,
  data: ProjectUpdateData,
): Promise<Project> {
  return apiFetch<Project>(`/projects/${id}`, { method: 'PATCH', body: data })
}

export function deleteProject(id: string): Promise<void> {
  return apiFetch<void>(`/projects/${id}`, { method: 'DELETE' })
}
