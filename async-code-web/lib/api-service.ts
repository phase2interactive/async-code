import { Project, Task, ProjectWithStats, ChatMessage } from '@/types'

const API_BASE = '/api';

// Helper function to get user ID header
function getUserIdHeader(userId?: string): HeadersInit {
    return userId ? { 'X-User-ID': userId } : {}
}

export class ApiService {
    // Project operations
    static async getProjects(userId: string): Promise<Project[]> {
        const response = await fetch(`${API_BASE}/projects`, {
            headers: getUserIdHeader(userId)
        })
        
        if (!response.ok) {
            throw new Error('Failed to fetch projects')
        }
        
        const data = await response.json()
        return data.projects || []
    }

    static async createProject(userId: string, projectData: {
        name: string
        description?: string
        repo_url: string
    }): Promise<Project> {
        const response = await fetch(`${API_BASE}/projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getUserIdHeader(userId)
            },
            body: JSON.stringify(projectData)
        })
        
        if (!response.ok) {
            throw new Error('Failed to create project')
        }
        
        const data = await response.json()
        return data.project
    }

    static async updateProject(userId: string, id: number, updates: Partial<Project>): Promise<Project> {
        const response = await fetch(`${API_BASE}/projects/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getUserIdHeader(userId)
            },
            body: JSON.stringify(updates)
        })
        
        if (!response.ok) {
            throw new Error('Failed to update project')
        }
        
        const data = await response.json()
        return data.project
    }

    static async deleteProject(userId: string, id: number): Promise<void> {
        const response = await fetch(`${API_BASE}/projects/${id}`, {
            method: 'DELETE',
            headers: getUserIdHeader(userId)
        })
        
        if (!response.ok) {
            throw new Error('Failed to delete project')
        }
    }

    static async getProject(userId: string, id: number): Promise<Project | null> {
        const response = await fetch(`${API_BASE}/projects/${id}`, {
            headers: getUserIdHeader(userId)
        })
        
        if (response.status === 404) {
            return null
        }
        
        if (!response.ok) {
            throw new Error('Failed to fetch project')
        }
        
        const data = await response.json()
        return data.project
    }

    // Task operations
    static async getTasks(userId: string, projectId?: number): Promise<any[]> {
        const url = projectId 
            ? `${API_BASE}/projects/${projectId}/tasks`
            : `${API_BASE}/tasks`
        
        const response = await fetch(url, {
            headers: getUserIdHeader(userId)
        })
        
        if (!response.ok) {
            throw new Error('Failed to fetch tasks')
        }
        
        const data = await response.json()
        return Object.values(data.tasks || {})
    }

    static async getTask(userId: string, id: number): Promise<Task | null> {
        const response = await fetch(`${API_BASE}/tasks/${id}`, {
            headers: getUserIdHeader(userId)
        })
        
        if (response.status === 404) {
            return null
        }
        
        if (!response.ok) {
            throw new Error('Failed to fetch task')
        }
        
        const data = await response.json()
        return data.task
    }

    static async startTask(userId: string, taskData: {
        prompt: string
        repo_url: string
        branch?: string
        github_token: string
        model?: string
        project_id?: number
    }): Promise<{ task_id: number }> {
        const response = await fetch(`${API_BASE}/start-task`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getUserIdHeader(userId)
            },
            body: JSON.stringify(taskData)
        })
        
        if (!response.ok) {
            throw new Error('Failed to start task')
        }
        
        const data = await response.json()
        return data
    }

    static async getTaskStatus(userId: string, taskId: number): Promise<any> {
        const response = await fetch(`${API_BASE}/task-status/${taskId}`, {
            headers: getUserIdHeader(userId)
        })
        
        if (!response.ok) {
            throw new Error('Failed to fetch task status')
        }
        
        const data = await response.json()
        return data.task
    }

    static async addChatMessage(userId: string, taskId: number, message: {
        role: string
        content: string
    }): Promise<Task> {
        const response = await fetch(`${API_BASE}/tasks/${taskId}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getUserIdHeader(userId)
            },
            body: JSON.stringify(message)
        })
        
        if (!response.ok) {
            throw new Error('Failed to add chat message')
        }
        
        const data = await response.json()
        return data.task
    }

    static async createPullRequest(userId: string, taskId: number, prData: {
        title?: string
        body?: string
        github_token: string
    }): Promise<{ pr_url: string; pr_number: number }> {
        const response = await fetch(`${API_BASE}/create-pr/${taskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getUserIdHeader(userId)
            },
            body: JSON.stringify(prData)
        })
        
        if (!response.ok) {
            throw new Error('Failed to create pull request')
        }
        
        const data = await response.json()
        return data
    }

    static async validateGitHubToken(token: string, repoUrl?: string): Promise<{
        user: string
        repo?: any
    }> {
        const response = await fetch(`${API_BASE}/validate-token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                github_token: token,
                repo_url: repoUrl
            })
        })
        
        if (!response.ok) {
            throw new Error('GitHub token validation failed')
        }
        
        const data = await response.json()
        return data
    }

    static async getGitDiff(userId: string, taskId: number): Promise<string> {
        const response = await fetch(`${API_BASE}/git-diff/${taskId}`, {
            headers: getUserIdHeader(userId)
        })
        
        if (!response.ok) {
            throw new Error('Failed to fetch git diff')
        }
        
        const data = await response.json()
        return data.git_diff || ''
    }

    // Utility functions
    static parseGitHubUrl(url: string): { owner: string, repo: string } {
        const match = url.match(/github\.com\/([^\/]+)\/([^\/]+?)(?:\.git)?(?:\/|$)/)
        if (!match) throw new Error('Invalid GitHub URL')
        return { owner: match[1], repo: match[2] }
    }
}