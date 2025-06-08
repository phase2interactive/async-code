import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

// Format git diff with basic syntax highlighting
export function formatDiff(diff: string): string {
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

// Parse git diff to extract statistics
export function parseDiffStats(diff: string): { additions: number; deletions: number; files: number } {
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