import { useId } from "react";
import { Link } from "react-router-dom";

// The frame around the sign-in, register and password pages
export function AuthCard({ title, children, backTo }: { title: string; children: React.ReactNode; backTo?: string }) {
    return (
        <main className="min-h-screen flex flex-col justify-center items-center gap-4 bg-gray-100 px-4 py-10">
            <div className="w-full max-w-[400px] flex flex-col gap-4">
                {backTo && (
                    <Link to={backTo} className="self-start flex items-center gap-2 tracking-wider hover:text-gray-600">
                        <i className="fa-solid fa-arrow-left" aria-hidden="true"></i>
                        BACK
                    </Link>
                )}
                <div className="flex flex-col justify-center border p-6 sm:p-10 gap-6 bg-white rounded-[20px] shadow-sm">
                    <h1 className="text-3xl sm:text-4xl">{title}</h1>
                    {children}
                </div>
            </div>
        </main>
    );
}

type TextFieldProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "id"> & {
    label: string;
    value: string;
    onChange: (value: string) => void;
};

// A labelled input in a rounded box; the box shows the keyboard focus, since the input
// inside it has no outline of its own
export function TextField({ label, value, onChange, className = "", ...input }: TextFieldProps) {
    const id = useId();
    return (
        <div className={`flex flex-col border p-2 rounded-[10px] gap-1 focus-within:ring-2 focus-within:ring-black ${className}`}>
            <label className="text-sm" htmlFor={id}>{label}</label>
            <input
                id={id}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="h-8 text-xl sm:text-2xl border-none focus:outline-hidden focus:ring-0 min-w-0"
                {...input}
            />
        </div>
    );
}
