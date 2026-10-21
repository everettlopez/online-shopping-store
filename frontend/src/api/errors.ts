import axios from "axios";

// Pull the FastAPI "detail" message out of a failed request
export function apiErrorMessage(err: unknown, fallback = "Something went wrong"): string {
    if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === "string") return detail;
        // Validation errors (422) come back as a list; show the first one
        if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return detail[0].msg;
    }
    return fallback;
}
