import { useEffect, useRef, type RefObject } from "react";

const FOCUSABLE = [
    "a[href]", "button:not([disabled])", "input:not([disabled])", "select:not([disabled])",
    "textarea:not([disabled])", "[tabindex]:not([tabindex='-1'])",
].join(",");

// Keyboard behavior for a hand-built dialog or drawer while it's open: focus moves into it
// (to an element marked data-autofocus, else the first control), Tab stays inside it, Esc
// closes it, the page behind doesn't scroll, and focus returns to what opened it.
// MUI's own Dialog does all this itself.
export function useDialog(ref: RefObject<HTMLElement | null>, open: boolean, onClose: () => void) {
    // The latest onClose, so callers can pass a new function each render
    const closeRef = useRef(onClose);
    useEffect(() => { closeRef.current = onClose; });

    useEffect(() => {
        const panel = ref.current;
        if (!open || !panel) return;

        const opener = document.activeElement as HTMLElement | null;
        const overflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";

        const focusable = () => [...panel.querySelectorAll<HTMLElement>(FOCUSABLE)].filter((el) => el.offsetParent !== null);
        (panel.querySelector<HTMLElement>("[data-autofocus]") ?? focusable()[0] ?? panel).focus();

        const onKey = (e: KeyboardEvent) => {
            // Focus in another dialog opened on top of this one (an MUI confirm): leave it be
            const active = document.activeElement;
            if (active && active !== document.body && !panel.contains(active)) return;

            if (e.key === "Escape") {
                e.preventDefault();
                closeRef.current();
            } else if (e.key === "Tab") {
                const items = focusable();
                if (items.length === 0) { e.preventDefault(); return; }
                const first = items[0], last = items[items.length - 1];
                if (e.shiftKey && (active === first || !panel.contains(active))) { e.preventDefault(); last.focus(); }
                else if (!e.shiftKey && active === last) { e.preventDefault(); first.focus(); }
            }
        };
        document.addEventListener("keydown", onKey);

        return () => {
            document.removeEventListener("keydown", onKey);
            document.body.style.overflow = overflow;
            opener?.focus();
        };
    }, [ref, open]);
}
