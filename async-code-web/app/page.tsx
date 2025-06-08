"use client";

import { useState, useEffect } from "react";
import { Github, GitBranch, Code2, ExternalLink, CheckCircle, Clock, XCircle, AlertCircle, FileText, Eye, GitCommit, Bell, Settings, LogOut, User, FolderGit2, Plus } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { formatDiff, parseDiffStats } from "@/lib/utils";
import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/contexts/auth-context";
import { ApiService } from "@/lib/api-service";
import { Project, Task } from "@/types";

interface TaskWithProject extends Task {
    project?: Project
}

export default function Home() {
    const { user, signOut } = useAuth();
    const [prompt, setPrompt] = useState("");
    const [selectedProject, setSelectedProject] = useState<string>("");
    const [branch, setBranch] = useState("main");
    const [githubToken, setGithubToken] = useState("");
    const [model, setModel] = useState("claude");
    const [currentTask, setCurrentTask] = useState<TaskWithProject | null>(null);
    const [tasks, setTasks] = useState<TaskWithProject[]>([]);
    const [projects, setProjects] = useState<Project[]>([]);
    const [gitDiff, setGitDiff] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [showNotification, setShowNotification] = useState(false);
    const [notificationMessage, setNotificationMessage] = useState("");
    const [diffStats, setDiffStats] = useState({ additions: 0, deletions: 0, files: 0 });

    // Initialize GitHub token from localStorage
    useEffect(() => {
        if (typeof window !== 'undefined') {
            const savedToken = localStorage.getItem('github-token');
            if (savedToken) {
                setGithubToken(savedToken);
            }
        }
    }, []);

    // Load initial data
    useEffect(() => {
        if (user?.id) {
            loadProjects();
            loadTasks();
        }
    }, [user?.id]);

    // Save GitHub token to localStorage whenever it changes
    useEffect(() => {
        if (typeof window !== 'undefined') {
            if (githubToken.trim()) {
                localStorage.setItem('github-token', githubToken);
            } else {
                localStorage.removeItem('github-token');
            }
        }
    }, [githubToken]);

    // Poll task status for running tasks
    useEffect(() => {
        if (!user?.id) return;

        const runningTasks = tasks.filter(task => task.status === "running" || task.status === "pending");
        if (runningTasks.length === 0) return;

        const interval = setInterval(async () => {
            try {
                const updatedTasks = await Promise.all(
                    runningTasks.map(task => ApiService.getTaskStatus(user.id, task.id))
                );

                setTasks(prevTasks => 
                    prevTasks.map(task => {
                        const updated = updatedTasks.find(t => t.id === task.id);
                        if (updated) {
                            // Check for status changes to show notifications
                            if (task.status !== updated.status) {
                                if (updated.status === "completed") {
                                    setNotificationMessage("🎉 Claude Code has finished making changes to your repository!");
                                    setShowNotification(true);
                                    setTimeout(() => setShowNotification(false), 5000);
                                } else if (updated.status === "failed") {
                                    setNotificationMessage("❌ Task failed. Please check the error details.");
                                    setShowNotification(true);
                                    setTimeout(() => setShowNotification(false), 5000);
                                }
                            }
                            return { ...task, ...updated };
                        }
                        return task;
                    })
                );

                // Update current task if it's being tracked
                if (currentTask) {
                    const updatedCurrentTask = updatedTasks.find(t => t.id === currentTask.id);
                    if (updatedCurrentTask) {
                        setCurrentTask(prev => ({ ...prev, ...updatedCurrentTask }));
                        
                        // Fetch git diff if task completed
                        if (updatedCurrentTask.status === "completed" && !gitDiff) {
                            try {
                                const diff = await ApiService.getGitDiff(user.id, updatedCurrentTask.id);
                                setGitDiff(diff);
                                const stats = parseDiffStats(diff);
                                setDiffStats(stats);
                            } catch (error) {
                                console.error('Error fetching git diff:', error);
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('Error polling task status:', error);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [tasks, currentTask, user?.id, gitDiff]);

    const loadProjects = async () => {
        if (!user?.id) return;
        
        try {
            const projectData = await ApiService.getProjects(user.id);
            setProjects(projectData);
        } catch (error) {
            console.error('Error loading projects:', error);
        }
    };

    const loadTasks = async () => {
        if (!user?.id) return;
        
        try {
            const taskData = await ApiService.getTasks(user.id);
            setTasks(taskData);
        } catch (error) {
            console.error('Error loading tasks:', error);
        }
    };

    const handleStartTask = async () => {
        if (!prompt.trim() || !githubToken.trim()) {
            alert('Please provide both a prompt and GitHub token');
            return;
        }

        if (!user?.id) {
            alert('User not authenticated');
            return;
        }

        let repoUrl = "";
        let projectId = undefined;

        if (selectedProject && selectedProject !== "custom") {
            const project = projects.find(p => p.id.toString() === selectedProject);
            if (project) {
                repoUrl = project.repo_url;
                projectId = project.id;
            }
        } else {
            // Custom repo URL - would need an input field for this
            alert('Custom repo URL input not implemented yet. Please select a project or create one first.');
            return;
        }

        setIsLoading(true);
        try {
            const response = await ApiService.startTask(user.id, {
                prompt: prompt.trim(),
                repo_url: repoUrl,
                branch: branch,
                github_token: githubToken,
                model: model,
                project_id: projectId
            });

            // Create a new task object for immediate display
            const newTask = {
                id: response.task_id,
                status: "pending",
                repo_url: repoUrl,
                target_branch: branch,
                agent: model,
                chat_messages: [{
                    role: 'user',
                    content: prompt.trim(),
                    timestamp: new Date().toISOString()
                }],
                created_at: new Date().toISOString(),
                user_id: user.id,
                project_id: projectId || null,
                project: projects.find(p => p.id === projectId)
            } as unknown as TaskWithProject;

            setCurrentTask(newTask);
            setTasks(prev => [newTask, ...prev]);
            setGitDiff("");
            setPrompt("");
        } catch (error) {
            alert(`Error starting task: ${error}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreatePR = async () => {
        if (!currentTask || currentTask.status !== "completed" || !user?.id) return;
        try {
            const prompt = (currentTask.chat_messages as any[])?.[0]?.content || '';
            const modelName = currentTask.agent === 'codex' ? 'Codex' : 'Claude Code';
            
            const response = await ApiService.createPullRequest(user.id, currentTask.id, {
                title: `${modelName}: ${prompt.substring(0, 50)}...`,
                body: `Automated changes generated by ${modelName}.\n\nPrompt: ${prompt}`,
                github_token: githubToken
            });

            alert(`Pull request created successfully! #${response.pr_number}`);
            window.open(response.pr_url, '_blank');
        } catch (error) {
            alert(`Error creating PR: ${error}`);
        }
    };

    const getStatusVariant = (status: string) => {
        switch (status) {
            case "pending": return "secondary";
            case "running": return "default";
            case "completed": return "default";
            case "failed": return "destructive";
            default: return "outline";
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "pending": return <Clock className="w-3 h-3" />;
            case "running": return <AlertCircle className="w-3 h-3" />;
            case "completed": return <CheckCircle className="w-3 h-3" />;
            case "failed": return <XCircle className="w-3 h-3" />;
            default: return null;
        }
    };

    return (
        <ProtectedRoute>
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
            {/* Notification Banner */}
            {showNotification && (
                <div className="bg-green-600 text-white px-6 py-3 text-center relative">
                    <div className="flex items-center justify-center gap-2">
                        <Bell className="w-4 h-4" />
                        <span>{notificationMessage}</span>
                    </div>
                    <button
                        onClick={() => setShowNotification(false)}
                        className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white hover:text-gray-200"
                    >
                        <XCircle className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* Header */}
            <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center">
                                <Code2 className="w-4 h-4 text-white" />
                            </div>
                            <div>
                                <h1 className="text-xl font-semibold text-slate-900">AI Code Automation</h1>
                                <p className="text-sm text-slate-500">Claude Code & Codex CLI Integration</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <Link href="/projects">
                                <Button variant="outline" className="gap-2">
                                    <FolderGit2 className="w-4 h-4" />
                                    Projects
                                </Button>
                            </Link>
                            
                            <Link href="/settings">
                                <Button variant="outline" className="gap-2">
                                    <Settings className="w-4 h-4" />
                                    Settings
                                </Button>
                            </Link>
                            
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="outline" className="gap-2">
                                        <User className="w-4 h-4" />
                                        {user?.email?.split('@')[0] || 'User'}
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" className="w-56">
                                    <div className="p-2">
                                        <p className="text-sm font-medium">{user?.email}</p>
                                        <p className="text-xs text-slate-500">Signed in</p>
                                    </div>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem onClick={signOut} className="gap-2 text-red-600">
                                        <LogOut className="w-4 h-4" />
                                        Sign Out
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-6 py-8 max-w-6xl">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column - Task Creation */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Main Input Card */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Code Generation Prompt</CardTitle>
                                <CardDescription>
                                    Describe the feature, bug fix, or enhancement you want AI to implement
                                </CardDescription>
                                {!githubToken.trim() && (
                                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-md">
                                        <div className="flex items-start gap-2 text-amber-800">
                                            <Github className="h-4 w-4 mt-0.5 flex-shrink-0" />
                                            <div className="text-sm">
                                                <strong>GitHub Token Required:</strong> Please configure your GitHub token in{" "}
                                                <Link href="/settings" className="underline hover:text-amber-900">
                                                    Settings
                                                </Link>{" "}
                                                to enable code generation.
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="space-y-2">
                                    <Label htmlFor="prompt">Your Prompt</Label>
                                    <Textarea
                                        id="prompt"
                                        value={prompt}
                                        onChange={(e) => setPrompt(e.target.value)}
                                        placeholder="e.g., Add a dark mode toggle to the navigation bar with persistent user preferences..."
                                        className="min-h-[120px] resize-none"
                                    />
                                </div>

                                <Separator />

                                {/* Repository Configuration */}
                                <div className="space-y-4">
                                    <h3 className="font-medium text-slate-900 flex items-center gap-2">
                                        <Github className="w-4 h-4" />
                                        Repository Settings
                                    </h3>
                                    
                                    {/* Project Selection - Full Width */}
                                    <div className="space-y-2">
                                        <Label htmlFor="project" className="flex items-center gap-2">
                                            <FolderGit2 className="w-3 h-3" />
                                            Project
                                        </Label>
                                        <Select value={selectedProject} onValueChange={setSelectedProject}>
                                            <SelectTrigger id="project" className="w-full">
                                                <SelectValue placeholder="Select a project" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {projects.map((project) => (
                                                    <SelectItem key={project.id} value={project.id.toString()}>
                                                        <div className="flex items-center gap-2 min-w-0">
                                                            <Github className="w-3 h-3 flex-shrink-0" />
                                                            <span className="truncate">{project.name}</span>
                                                            <span className="text-slate-500 text-xs flex-shrink-0">
                                                                ({project.repo_owner}/{project.repo_name})
                                                            </span>
                                                        </div>
                                                    </SelectItem>
                                                ))}
                                                <SelectItem value="custom">Custom Repository URL</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        {projects.length === 0 && (
                                            <p className="text-sm text-slate-500">
                                                No projects found.{" "}
                                                <Link href="/projects" className="text-blue-600 hover:underline">
                                                    Create a project first
                                                </Link>
                                            </p>
                                        )}
                                    </div>

                                    {/* Branch and Model in a responsive grid */}
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label htmlFor="branch" className="flex items-center gap-2">
                                                <GitBranch className="w-3 h-3" />
                                                Branch
                                            </Label>
                                            <Input
                                                id="branch"
                                                value={branch}
                                                onChange={(e) => setBranch(e.target.value)}
                                                placeholder="main"
                                                className="w-full"
                                            />
                                        </div>
                                        
                                        <div className="space-y-2">
                                            <Label htmlFor="model" className="flex items-center gap-2">
                                                <Code2 className="w-3 h-3" />
                                                AI Model
                                            </Label>
                                            <Select value={model} onValueChange={setModel}>
                                                <SelectTrigger id="model" className="w-full">
                                                    <SelectValue placeholder="Select an AI model" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="claude">
                                                        <div className="flex flex-col items-start">
                                                            <span className="font-medium">Claude Code</span>
                                                            <span className="text-xs text-slate-500">Anthropic's advanced coding model</span>
                                                        </div>
                                                    </SelectItem>
                                                    <SelectItem value="codex">
                                                        <div className="flex flex-col items-start">
                                                            <span className="font-medium">Codex CLI</span>
                                                            <span className="text-xs text-slate-500">OpenAI's lightweight coding agent</span>
                                                        </div>
                                                    </SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-end pt-2">
                                    <Button
                                        onClick={handleStartTask}
                                        disabled={isLoading || !selectedProject || !prompt.trim() || !githubToken.trim()}
                                        size="lg"
                                        className="gap-2 min-w-[140px]"
                                    >
                                        <Code2 className="w-4 h-4" />
                                        {isLoading ? 'Starting...' : 'Start Coding'}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Current Task Status */}
                        {currentTask && (
                            <Card>
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <div className="space-y-1">
                                            <CardTitle className="flex items-center gap-2">
                                                <Badge variant={getStatusVariant(currentTask.status || '')} className="gap-1">
                                                    {getStatusIcon(currentTask.status || '')}
                                                    {currentTask.status}
                                                </Badge>
                                                Task Status {currentTask.agent && `(${currentTask.agent.toUpperCase()})`}
                                            </CardTitle>
                                            <CardDescription>
                                                {new Date(currentTask.created_at || '').toLocaleString()} • {currentTask.project?.name || 'Custom Repository'}
                                            </CardDescription>
                                        </div>
                                        {currentTask.status === "completed" && (
                                            <div className="flex gap-2">
                                                <Button variant="outline" asChild>
                                                    <Link href={`/tasks/${currentTask.id}`}>
                                                        <Eye className="w-4 h-4 mr-1" />
                                                        View Details
                                                    </Link>
                                                </Button>
                                                <Button onClick={handleCreatePR} className="gap-2">
                                                    <ExternalLink className="w-4 h-4" />
                                                    Create PR
                                                </Button>
                                            </div>
                                        )}
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div>
                                        <Label className="text-sm font-medium">Prompt</Label>
                                        <p className="text-sm text-slate-700 mt-1 p-3 bg-slate-50 rounded-md">
                                            {(currentTask.chat_messages as any[])?.[0]?.content || 'No prompt available'}
                                        </p>
                                    </div>

                                    {/* Running Status Indicator */}
                                    {currentTask.status === "running" && (
                                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                            <div className="flex items-center gap-3">
                                                <div className="animate-spin">
                                                    <AlertCircle className="w-5 h-5 text-blue-600" />
                                                </div>
                                                <div>
                                                    <div className="font-medium text-blue-900">AI is working on your code...</div>
                                                    <div className="text-sm text-blue-700 mt-1">
                                                        Analyzing repository, making changes, and preparing commit. This may take a few minutes.
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="mt-3 bg-blue-100 rounded-full h-2">
                                                <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                                            </div>
                                        </div>
                                    )}

                                    {currentTask.error && (
                                        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                                            <div className="flex items-center gap-2 text-red-800">
                                                <XCircle className="w-4 h-4" />
                                                <span className="font-medium">Error</span>
                                            </div>
                                            <p className="text-sm text-red-700 mt-1">
                                                {currentTask.error}
                                            </p>
                                        </div>
                                    )}

                                    {/* Git Diff Display */}
                                    {gitDiff && (
                                        <div className="space-y-4">
                                            <div className="flex items-center justify-between">
                                                <Label className="text-sm font-medium flex items-center gap-2">
                                                    <CheckCircle className="w-4 h-4 text-green-600" />
                                                    Code Review
                                                </Label>
                                                <div className="flex items-center gap-4 text-sm">
                                                    <div className="flex items-center gap-1">
                                                        <FileText className="w-3 h-3 text-slate-500" />
                                                        <span className="text-slate-600">{diffStats.files} files</span>
                                                    </div>
                                                    <div className="flex items-center gap-1">
                                                        <span className="text-green-600">+{diffStats.additions}</span>
                                                        <span className="text-red-600">-{diffStats.deletions}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            {/* Diff Statistics Summary */}
                                            <div className="bg-slate-50 rounded-lg p-4 border">
                                                <div className="flex items-center gap-6 text-sm">
                                                    <div className="flex items-center gap-2">
                                                        <GitCommit className="w-4 h-4 text-slate-500" />
                                                        <span className="font-medium">Commit:</span>
                                                        <code className="bg-slate-200 px-2 py-1 rounded text-xs">
                                                            {currentTask.commit_hash?.substring(0, 8)}
                                                        </code>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Eye className="w-4 h-4 text-slate-500" />
                                                        <span>Ready for review</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Enhanced Diff Display */}
                                            <div className="bg-slate-900 rounded-lg overflow-hidden border">
                                                <div className="bg-slate-800 px-4 py-2 text-sm text-slate-200 font-medium">
                                                    Git Diff
                                                </div>
                                                <div className="p-4 overflow-x-auto">
                                                    <pre className="text-sm text-slate-100 whitespace-pre-wrap">
                                                        {formatDiff(gitDiff)}
                                                    </pre>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        )}
                    </div>

                    {/* Right Column - Task List */}
                    <div className="space-y-6">
                        <Card>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Recent Tasks</CardTitle>
                                    <Link href="/tasks">
                                        <Button variant="outline" size="sm">View All</Button>
                                    </Link>
                                </div>
                                <CardDescription>
                                    Latest automation tasks across all projects
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {tasks.length === 0 ? (
                                    <div className="text-center py-8 text-slate-500">
                                        <Code2 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                        <p className="text-sm">No tasks yet</p>
                                        <p className="text-xs">Start your first automation above</p>
                                    </div>
                                ) : (
                                    tasks.slice(0, 10).map((task) => (
                                        <div key={task.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <Badge variant={getStatusVariant(task.status || '')} className="gap-1">
                                                        {getStatusIcon(task.status || '')}
                                                        {task.status}
                                                    </Badge>
                                                    <span className="text-xs text-slate-500">
                                                        {task.agent?.toUpperCase()}
                                                    </span>
                                                </div>
                                                <p className="text-sm font-medium text-slate-900 truncate mt-1">
                                                    {(task.chat_messages as any[])?.[0]?.content?.substring(0, 50) || 'No prompt'}...
                                                </p>
                                                <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
                                                    {task.project ? (
                                                        <>
                                                            <FolderGit2 className="w-3 h-3" />
                                                            {task.project.name}
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Github className="w-3 h-3" />
                                                            Custom
                                                        </>
                                                    )}
                                                    <span>•</span>
                                                    <span>{new Date(task.created_at || '').toLocaleDateString()}</span>
                                                </div>
                                            </div>
                                            <Link href={`/tasks/${task.id}`}>
                                                <Button variant="ghost" size="sm">
                                                    <Eye className="w-3 h-3" />
                                                </Button>
                                            </Link>
                                        </div>
                                    ))
                                )}
                            </CardContent>
                        </Card>

                        {/* Quick Actions */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg">Quick Actions</CardTitle>
                            </CardHeader>
                            <CardContent className="p-2">
                                <Link href="/projects">
                                    <Button variant="outline" className="mb-2 w-full justify-start gap-3 h-12 px-4">
                                        <FolderGit2 className="w-5 h-5" />
                                        <span className="font-medium">Manage Projects</span>
                                    </Button>
                                </Link>
                                <Link href="/settings">
                                    <Button variant="outline" className="mb-2 w-full justify-start gap-3 h-12 px-4">
                                        <Settings className="w-5 h-5" />
                                        <span className="font-medium">Settings</span>
                                    </Button>
                                </Link>
                                <Link href="/projects">
                                    <Button variant="outline" className="mb-2 w-full justify-start gap-3 h-12 px-4">
                                        <Plus className="w-5 h-5" />
                                        <span className="font-medium">New Project</span>
                                    </Button>
                                </Link>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </main>
        </div>
        </ProtectedRoute>
    );
}
