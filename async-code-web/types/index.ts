export interface Task {
    id: string;
    status: string;
    prompt: string;
    repo_url: string;
    branch: string;
    model?: string;
    commit_hash?: string;
    error?: string;
    created_at: number;
}