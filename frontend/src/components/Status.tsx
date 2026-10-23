import { Link } from "react-router-dom";

// Shared loading, error and empty states, so every page waits, fails and comes up empty the same way

export function Spinner({ className = "h-8 w-8" }: { className?: string }) {
    return (
        <span
            className={`inline-block animate-spin rounded-full border-2 border-gray-300 border-t-black ${className}`}
            aria-hidden="true"
        />
    );
}

// A spinner with words for screen readers; `page` gives it the height of a page section
export function LoadingState({ label = "Loading", page = false }: { label?: string; page?: boolean }) {
    return (
        <div role="status" className={`flex flex-col items-center justify-center gap-3 text-gray-500 ${page ? "min-h-[50vh]" : "py-10"}`}>
            <Spinner />
            <span className="text-sm tracking-wider">{label}...</span>
        </div>
    );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
    return (
        <div role="alert" className="flex flex-col items-center gap-3 py-10 text-center">
            <p className="tracking-wider text-gray-600">{message}</p>
            {onRetry && (
                <button onClick={onRetry} className="border border-black rounded-full px-6 py-1.5 tracking-wider hover:bg-black hover:text-white transition">
                    Try again
                </button>
            )}
        </div>
    );
}

interface EmptyStateProps {
    title: string;
    message?: string;
    action?: { to: string; label: string };
}

export function EmptyState({ title, message, action }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center gap-3 py-10 px-4 text-center">
            <p className="text-lg tracking-wider">{title}</p>
            {message && <p className="text-gray-500">{message}</p>}
            {action && (
                <Link to={action.to} className="bg-black text-white rounded-full px-8 py-2 tracking-wider hover:bg-gray-800 transition">
                    {action.label}
                </Link>
            )}
        </div>
    );
}
