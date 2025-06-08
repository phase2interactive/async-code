"use client";

import { useState, useEffect } from "react";
import { Github, GitBranch, Code2, ExternalLink, CheckCircle, Clock, XCircle, AlertCircle, FileText, Eye, GitCommit, Bell, Settings } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";


interface Task {
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

// Parse git diff to extract statistics
function parseDiffStats(diff: string): { additions: number; deletions: number; files: number } {
    if (!diff) return { additions: 0, deletions: 0, files: 0 };
    
    const lines = diff.split('\n');
    let additions = 0;
    let deletions = 0;
    const files = new Set<string>();
    
    for (const line of lines) {
        if (line.startsWith('+++') || line.startsWith('---')) {
            const filePath = line.substring(4);
            if (filePath !== '/dev/null') {
                files.add(filePath);
            }
        } else if (line.startsWith('+') && !line.startsWith('+++')) {
            additions++;
        } else if (line.startsWith('-') && !line.startsWith('---')) {
            deletions++;
        }
    }
    
    return { additions, deletions, files: files.size };
}

// Format git diff with basic syntax highlighting
function formatDiff(diff: string): string {
    if (!diff) return '';
    
    return diff.split('\n').map(line => {
        if (line.startsWith('+++') || line.startsWith('---')) {
            return line; // File headers
        } else if (line.startsWith('@@')) {
            return line; // Hunk headers
        } else if (line.startsWith('+') && !line.startsWith('+++')) {
            return line; // Additions
        } else if (line.startsWith('-') && !line.startsWith('---')) {
            return line; // Deletions
        }
        return line; // Context lines
    }).join('\n');
}

export default function Home() {
    const [prompt, setPrompt] = useState("");
    const [repoUrl, setRepoUrl] = useState("https://github.com/ObservedObserver/streamlit-react");
    const [branch, setBranch] = useState("main");
    const [githubToken, setGithubToken] = useState("");
    const [model, setModel] = useState("claude");
    const [currentTask, setCurrentTask] = useState<Task | null>(null);
    const [gitDiff, setGitDiff] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [showNotification, setShowNotification] = useState(false);
    const [notificationMessage, setNotificationMessage] = useState("");
    const [diffStats, setDiffStats] = useState({ additions: 0, deletions: 0, files: 0 });

    const API_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost' 
        ? 'http://localhost:5000' 
        : '/api';

    // Initialize GitHub token from localStorage
    useEffect(() => {
        if (typeof window !== 'undefined') {
            const savedToken = localStorage.getItem('github-token');
            if (savedToken) {
                setGithubToken(savedToken);
            }
        }
    }, []);

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

    // Poll task status
    useEffect(() => {
        if (currentTask && (currentTask.status === "running" || currentTask.status === "pending")) {
            console.log(`Starting polling for task ${currentTask.id} with status: ${currentTask.status}`);
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`${API_BASE}/task-status/${currentTask.id}`);
                    const data = await response.json();
                    
                    console.log(`Polling response for task ${currentTask.id}:`, data);
                    
                    if (data.status === 'success') {
                        const previousStatus = currentTask.status;
                        setCurrentTask(data.task);
                        
                        if (data.task.status === "completed" && previousStatus !== "completed") {
                            // Task just completed - show notification
                            setNotificationMessage("🎉 Claude Code has finished making changes to your repository!");
                            setShowNotification(true);
                            setTimeout(() => setShowNotification(false), 5000);
                            
                            // Fetch git diff
                            const diffResponse = await fetch(`${API_BASE}/git-diff/${currentTask.id}`);
                            const diffData = await diffResponse.json();
                            if (diffData.status === 'success') {
                                setGitDiff(diffData.git_diff);
                                // Parse diff statistics
                                const stats = parseDiffStats(diffData.git_diff);
                                setDiffStats(stats);
                            }
                        } else if (data.task.status === "failed" && previousStatus !== "failed") {
                            // Task just failed - show notification
                            setNotificationMessage("❌ Task failed. Please check the error details below.");
                            setShowNotification(true);
                            setTimeout(() => setShowNotification(false), 5000);
                        }
                    }
                } catch (error) {
                    console.error('Error polling task status:', error);
                }
            }, 2000);

            return () => {
                console.log(`Stopping polling for task ${currentTask.id}`);
                clearInterval(interval);
            };
        }
    }, [currentTask, API_BASE]);

    const handleStartTask = async () => {
        if (!prompt.trim() || !githubToken.trim()) {
            alert('Please provide both a prompt and GitHub token');
            return;
        }

        setIsLoading(true);
        try {
            const response = await fetch(`${API_BASE}/start-task`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt.trim(),
                    repo_url: repoUrl,
                    branch: branch,
                    github_token: githubToken,
                    model: model
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                setCurrentTask({
                    id: data.task_id,
                    status: "pending",
                    prompt: prompt.trim(),
                    repo_url: repoUrl,
                    branch: branch,
                    model: model,
                    created_at: Date.now()
                });
                setGitDiff("");
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            alert(`Error starting task: ${error}`);
        } finally {
            setIsLoading(false);
        }
    };



    const handleCreatePR = async () => {
        if (!currentTask || currentTask.status !== "completed") return;

        try {
            const modelName = currentTask.model === 'codex' ? 'Codex' : 'Claude Code';
            const response = await fetch(`${API_BASE}/create-pr/${currentTask.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: `${modelName}: ${currentTask.prompt.substring(0, 50)}...`,
                    body: `Automated changes generated by ${modelName}.\n\nPrompt: ${currentTask.prompt}`
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                alert(`Pull request created successfully! #${data.pr_number}`);
                window.open(data.pr_url, '_blank');
            } else {
                alert(`Error creating PR: ${data.error}`);
            }
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
                        <Link href="/settings">
                            <Button
                                variant="outline"
                                className="gap-2"
                            >
                                <Settings className="w-4 h-4" />
                                Settings
                            </Button>
                        </Link>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-6 py-8 max-w-4xl">
                <div className="text-center mb-8">
                    <h2 className="text-3xl font-bold text-slate-900 mb-2">
                        What are we coding next?
                    </h2>
                    <p className="text-slate-600">
                        Describe what you want to build and your selected AI model will analyze your repository and make the necessary changes
                    </p>
                </div>

                <div className="space-y-6">

                    {/* Main Input Card */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Code Generation Prompt</CardTitle>
                            <CardDescription>
                                Describe the feature, bug fix, or enhancement you want Claude to implement
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
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="repo-url">Repository URL</Label>
                                        <Input
                                            id="repo-url"
                                            type="url"
                                            value={repoUrl}
                                            onChange={(e) => setRepoUrl(e.target.value)}
                                            placeholder="https://github.com/owner/repo"
                                        />
                                    </div>
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
                                        />
                                    </div>
                                </div>
                                
                                {/* Model Selection */}
                                <div className="space-y-2">
                                    <Label htmlFor="model" className="flex items-center gap-2">
                                        <Code2 className="w-3 h-3" />
                                        AI Model
                                    </Label>
                                    <Select value={model} onValueChange={setModel}>
                                        <SelectTrigger id="model">
                                            <SelectValue placeholder="Select an AI model" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="claude">
                                                Claude Code - Anthropic&apos;s advanced coding model
                                            </SelectItem>
                                            <SelectItem value="codex">
                                                Codex CLI - OpenAI&apos;s lightweight coding agent
                                            </SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <p className="text-sm text-slate-600">
                                        Choose between Claude Code or Codex CLI for your automation needs
                                    </p>
                                </div>
                            </div>

                            <div className="flex justify-end">
                                <Button
                                    onClick={handleStartTask}
                                    disabled={isLoading || (currentTask?.status === "running")}
                                    size="lg"
                                    className="gap-2"
                                >
                                    <Code2 className="w-4 h-4" />
                                    {isLoading && 'Starting...'}
                                    {!isLoading && 'Start Coding'}
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
                                            <Badge variant={getStatusVariant(currentTask.status)} className="gap-1">
                                                {getStatusIcon(currentTask.status)}
                                                {currentTask.status}
                                            </Badge>
                                            Task Status {currentTask.model && `(${currentTask.model.toUpperCase()})`}
                                        </CardTitle>
                                        <CardDescription>
                                            {new Date(currentTask.created_at).toLocaleString()} • {currentTask.repo_url}
                                        </CardDescription>
                                    </div>
{currentTask.status === "completed" && !gitDiff && (
                                        <Button
                                            onClick={handleCreatePR}
                                            variant="default"
                                            className="gap-2"
                                        >
                                            <ExternalLink className="w-4 h-4" />
                                            Create PR
                                        </Button>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <Label className="text-sm font-medium">Prompt</Label>
                                    <p className="text-sm text-slate-700 mt-1 p-3 bg-slate-50 rounded-md">
                                        {currentTask.prompt}
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
                                                <div className="font-medium text-blue-900">Claude is working on your code...</div>
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
                                            <div className="bg-slate-800 px-4 py-2 border-b border-slate-700">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-slate-300 text-sm font-medium">Changes</span>
                                                    <div className="flex items-center gap-2 text-xs text-slate-400">
                                                        <span className="bg-green-600/20 text-green-400 px-2 py-1 rounded">
                                                            +{diffStats.additions}
                                                        </span>
                                                        <span className="bg-red-600/20 text-red-400 px-2 py-1 rounded">
                                                            -{diffStats.deletions}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="max-h-96 overflow-y-auto">
                                                <pre className="text-sm text-slate-100 p-4 overflow-x-auto">
                                                    {formatDiff(gitDiff)}
                                                </pre>
                                            </div>
                                        </div>

                                        {/* Action Buttons */}
                                        <div className="flex items-center justify-between pt-2">
                                            <div className="text-sm text-slate-600">
                                                Review the changes above, then create a pull request to merge them.
                                            </div>
                                            <div className="flex gap-2">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => navigator.clipboard.writeText(gitDiff)}
                                                    className="gap-2"
                                                >
                                                    <FileText className="w-3 h-3" />
                                                    Copy Diff
                                                </Button>
                                                <Button
                                                    onClick={handleCreatePR}
                                                    size="sm"
                                                    className="gap-2"
                                                >
                                                    <ExternalLink className="w-3 h-3" />
                                                    Create PR
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}

                    {/* Instructions */}
                    {!currentTask && (
                        <Card className="bg-slate-50 border-slate-200">
                            <CardContent className="text-center py-8">
                                <Code2 className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-slate-900 mb-2">
                                    Ready to Start Coding
                                </h3>
                                <p className="text-slate-600 max-w-md mx-auto">
                                    Enter a detailed prompt describing what you want to build. Your selected AI model will analyze your repository 
                                    and implement the necessary changes automatically.
                                </p>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </main>
        </div>
    );
}
