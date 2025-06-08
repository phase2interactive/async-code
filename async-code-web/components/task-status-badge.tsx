import { Clock, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface TaskStatusBadgeProps {
    status: string;
    className?: string;
}

export function TaskStatusBadge({ status, className }: TaskStatusBadgeProps) {
    switch (status) {
        case "pending":
            return (
                <Badge variant="secondary" className={cn("gap-1", className)}>
                    <Clock className="w-4 h-4" />
                    pending
                </Badge>
            );
        
        case "running":
            return (
                <Badge variant="default" className={cn("gap-1", className)}>
                    <AlertCircle className="w-4 h-4" />
                    running
                </Badge>
            );
        
        case "completed":
            return (
                <Badge variant="secondary" className={cn("gap-1", className, "bg-green-600 text-white dark:bg-green-600 border-green-600")}>
                    <CheckCircle className="w-4 h-4" />
                    completed
                </Badge>
            );
        
        case "failed":
            return (
                <Badge variant="destructive" className={cn("gap-1", className)}>
                    <XCircle className="w-4 h-4" />
                    failed
                </Badge>
            );
        
        default:
            return (
                <Badge variant="outline" className={cn("gap-1", className)}>
                    {status}
                </Badge>
            );
    }
} 