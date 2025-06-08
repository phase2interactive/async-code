import { supabase } from './supabase'
import { Project, Task, ProjectWithStats, ChatMessage } from '@/types'

export class SupabaseService {
    // Project operations
    static async getProjects(): Promise<ProjectWithStats[]> {
        const { data, error } = await supabase
            .from('projects')
            .select(`
                *,
                tasks (
                    id,
                    status
                )
            `)
            .order('created_at', { ascending: false })

        if (error) throw error

        // Add task statistics
        return data?.map((project: any) => ({
            ...project,
            task_count: project.tasks?.length || 0,
            completed_tasks: project.tasks?.filter((t: any) => t.status === 'completed').length || 0,
            active_tasks: project.tasks?.filter((t: any) => t.status === 'running').length || 0
        })) || []
    }

    static async createProject(projectData: {
        name: string
        description?: string
        repo_url: string
        repo_name: string
        repo_owner: string
        settings?: any
    }): Promise<Project> {
        const { data, error } = await supabase
            .from('projects')
            .insert([projectData])
            .select()
            .single()

        if (error) throw error
        return data
    }

    static async updateProject(id: number, updates: Partial<Project>): Promise<Project> {
        const { data, error } = await supabase
            .from('projects')
            .update(updates)
            .eq('id', id)
            .select()
            .single()

        if (error) throw error
        return data
    }

    static async deleteProject(id: number): Promise<void> {
        const { error } = await supabase
            .from('projects')
            .delete()
            .eq('id', id)

        if (error) throw error
    }

    static async getProject(id: number): Promise<Project | null> {
        const { data, error } = await supabase
            .from('projects')
            .select('*')
            .eq('id', id)
            .single()

        if (error) {
            if (error.code === 'PGRST116') return null // Not found
            throw error
        }
        return data
    }

    // Task operations
    static async getTasks(projectId?: number): Promise<Task[]> {
        let query = supabase
            .from('tasks')
            .select(`
                *,
                project:projects (
                    id,
                    name,
                    repo_name,
                    repo_owner
                )
            `)

        if (projectId) {
            query = query.eq('project_id', projectId)
        }

        const { data, error } = await query.order('created_at', { ascending: false })

        if (error) throw error
        return data || []
    }

    static async getTask(id: number): Promise<Task | null> {
        const { data, error } = await supabase
            .from('tasks')
            .select(`
                *,
                project:projects (
                    id,
                    name,
                    repo_name,
                    repo_owner
                )
            `)
            .eq('id', id)
            .single()

        if (error) {
            if (error.code === 'PGRST116') return null // Not found
            throw error
        }
        return data
    }

    static async createTask(taskData: {
        project_id?: number
        repo_url?: string
        target_branch?: string
        agent?: string
        chat_messages?: ChatMessage[]
    }): Promise<Task> {
        const { data, error } = await supabase
            .from('tasks')
            .insert([{
                ...taskData,
                status: 'pending'
            }])
            .select()
            .single()

        if (error) throw error
        return data
    }

    static async updateTask(id: number, updates: Partial<Task>): Promise<Task> {
        const { data, error } = await supabase
            .from('tasks')
            .update(updates)
            .eq('id', id)
            .select()
            .single()

        if (error) throw error
        return data
    }

    static async addChatMessage(taskId: number, message: ChatMessage): Promise<Task> {
        // First get the current task to get existing messages
        const { data: task, error: fetchError } = await supabase
            .from('tasks')
            .select('chat_messages')
            .eq('id', taskId)
            .single()

        if (fetchError) throw fetchError

        const existingMessages = (task.chat_messages as ChatMessage[]) || []
        const updatedMessages = [...existingMessages, message]

        const { data, error } = await supabase
            .from('tasks')
            .update({ 
                chat_messages: updatedMessages,
                updated_at: new Date().toISOString()
            })
            .eq('id', taskId)
            .select()
            .single()

        if (error) throw error
        return data
    }

    // User operations
    static async getCurrentUser() {
        const { data: { user } } = await supabase.auth.getUser()
        return user
    }

    static async getUserProfile() {
        const { data: { user } } = await supabase.auth.getUser()
        if (!user) return null

        const { data, error } = await supabase
            .from('users')
            .select('*')
            .eq('id', user.id)
            .single()

        if (error) {
            if (error.code === 'PGRST116') return null // Not found
            throw error
        }
        return data
    }

    static async updateUserProfile(updates: {
        full_name?: string
        github_username?: string
        github_token?: string
        preferences?: any
    }) {
        const { data: { user } } = await supabase.auth.getUser()
        if (!user) throw new Error('No authenticated user')

        const { data, error } = await supabase
            .from('users')
            .update(updates)
            .eq('id', user.id)
            .select()
            .single()

        if (error) throw error
        return data
    }

    // Utility functions
    static parseGitHubUrl(url: string): { owner: string, repo: string } {
        const match = url.match(/github\.com\/([^\/]+)\/([^\/]+?)(?:\.git)?(?:\/|$)/)
        if (!match) throw new Error('Invalid GitHub URL')
        return { owner: match[1], repo: match[2] }
    }
}