import { Project, Task, ProjectWithStats, ChatMessage } from '@/types'
import { jwtService } from './jwt-service'

const API_BASE = '/api';

// Helper function to get auth headers
function getAuthHeaders(): HeadersInit {
    const token = jwtService.getAccessToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {}
}

export class ApiService {
    // Project operations
    static async getProjects(): Promise<Project[]> {
        const response = await fetch(`${API_BASE}/projects`, {
            headers: getAuthHeaders()
        })
        
        if (!response.ok) {
            throw new Error('Failed to fetch projects')
        }
        
        const data = await response.json()
        return data.projects || []
    }

    static async createProject(projectData: {
        name: string
        description?: string
        repo_url: string
    }): Promise<Project> {
        const response = await fetch(`${API_BASE}/projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify(projectData)
        })
        
        if (!response.ok) {
            throw new Error('Failed to create project')
        }
        
        const data = await response.json()
        return data.project
    }

    static async updateProject(id: number, updates: Partial<Project>): Promise<Project> {
        const response = await fetch(`${API_BASE}/projects/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify(updates)
        })
        
        if (!response.ok) {
            throw new Error('Failed to update project')
        }
        
        const data = await response.json()
        return data.project
    }

    static async deleteProject(id: number): Promise<void> {
        const response = await fetch(`${API_BASE}/projects/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        })
        
        if (!response.ok) {
            throw new Error('Failed to delete project')
        }
    }

    static async getProject(id: number): Promise<Project | null> {
        const response = await fetch(`${API_BASE}/projects/${id}`, {
            headers: getAuthHeaders()
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
    static async getTasks(projectId?: number): Promise<any[]> {
        const url = projectId 
            ? `${API_BASE}/projects/${projectId}/tasks`
            : `${API_BASE}/tasks`
        
        const response = await fetch(url, {
            headers: getAuthHeaders()
        })
        
        if (!response.ok) {
            throw new Error('Failed to fetch tasks')
        }
        
        const data = await response.json()
        return Object.values(data.tasks || {})
    }

    static async getTask(id: number): Promise<Task | null> {
        const response = await fetch(`${API_BASE}/tasks/${id}`, {
            headers: getAuthHeaders()
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

    static async startTask(taskData: {
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
                ...getAuthHeaders()
            },
            body: JSON.stringify(taskData)
        })
        
        if (!response.ok) {
            throw new Error('Failed to start task')
        }
        
        const data = await response.json()
        return data
    }

    static async getTaskStatus(taskId: number): Promise<any> {
        const response = await fetch(`${API_BASE}/task-status/${taskId}`, {
            headers: getAuthHeaders()
        })
        
        if (!response.ok) {
            throw new Error('Failed to fetch task status')
        }
        
        const data = await response.json()
        return data.task
    }

    static async addChatMessage(taskId: number, message: {
        role: string
        content: string
    }): Promise<Task> {
        const response = await fetch(`${API_BASE}/tasks/${taskId}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify(message)
        })
        
        if (!response.ok) {
            throw new Error('Failed to add chat message')
        }
        
        const data = await response.json()
        return data.task
    }

    static async createPullRequest(taskId: number, prData: {
        title?: string
        body?: string
        github_token: string
    }): Promise<{ pr_url: string; pr_number: number }> {
        const response = await fetch(`${API_BASE}/create-pr/${taskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
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

    static async getGitDiff(taskId: number): Promise<string> {
        const response = await fetch(`${API_BASE}/git-diff/${taskId}`, {
            headers: getAuthHeaders()
        })
        
        if (!response.ok) {
            throw new Error('Failed to fetch git diff')
        }
        
        const data = await response.json()
        return data.git_diff || ''
    }

    // Authentication methods
    static async generateToken(userId: string): Promise<{
        access_token: string
        refresh_token: string
        expires_in: number
    }> {
        const response = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        })
        
        if (!response.ok) {
            throw new Error('Failed to generate token')
        }
        
        return response.json()
    }
    
    static async refreshToken(refreshToken: string): Promise<{
        access_token: string
        expires_in: number
    }> {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        })
        
        if (!response.ok) {
            throw new Error('Failed to refresh token')
        }
        
        return response.json()
    }
    
    static async verifyToken(): Promise<boolean> {
        const response = await fetch(`${API_BASE}/auth/verify`, {
            headers: getAuthHeaders()
        })
        
        return response.ok
    }

    // Utility functions
    static parseGitHubUrl(url: string): { owner: string, repo: string } {
        const match = url.match(/github\.com\/([^\/]+)\/([^\/]+?)(?:\.git)?(?:\/|$)/)
        if (!match) throw new Error('Invalid GitHub URL')
        return { owner: match[1], repo: match[2] }
    }
}