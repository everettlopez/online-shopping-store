import { useEffect, useId, useRef } from "react";

interface DrawerProps {
    open: boolean;
    onClose: () => void;
    title: string;
    side?: "left" | "right";
    children: React.ReactNode;
    footer?: React.ReactNode;
}

// A panel that slides over the page on small screens (the header menu, the product filters).
// Esc, the backdrop and the close button close it; focus moves into it and back again.
export default function Drawer({ open, onClose, title, side = "left", children, footer }: DrawerProps) {
    const titleId = useId();
    const closeRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
        if (!open) return;

        const opener = document.activeElement as HTMLElement | null;
        const overflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        closeRef.current?.focus();

        const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
        document.addEventListener("keydown", onKey);

        return () => {
            document.removeEventListener("keydown", onKey);
            document.body.style.overflow = overflow;
            opener?.focus();
        };
    }, [open, onClose]);

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-50">
            <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />

            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby={titleId}
                className={`absolute top-0 bottom-0 ${side === "left" ? "left-0" : "right-0"} w-80 max-w-[85vw] bg-white flex flex-col shadow-lg`}
            >
                <div className="flex items-center justify-between p-5 border-b">
                    <h2 id={titleId} className="text-lg tracking-widest">{title}</h2>
                    <button ref={closeRef} onClick={onClose} aria-label="Close" className="text-2xl leading-none px-2">
                        <i className="fa-solid fa-xmark" aria-hidden="true"></i>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-5">{children}</div>

                {footer && <div className="p-5 border-t">{footer}</div>}
            </div>
        </div>
    );
}
