// Preset sizes and colors offered when an admin creates or edits a product. Both are
// free text on the server, so these are only suggestions: anything else can be typed.

export interface SizeGroup {
    name: string;
    sizes: string[];
}

const range = (from: number, to: number, step = 1) =>
    Array.from({ length: Math.floor((to - from) / step) + 1 }, (_, i) => from + i * step);

const WAISTS = range(26, 44);
const INSEAMS = [28, 30, 32, 34, 36];

export const SIZE_GROUPS: SizeGroup[] = [
    { name: "General", sizes: ["1SZ"] },
    { name: "Tops / letter", sizes: ["XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL"] },
    {
        name: "Pants (waist x inseam)",
        sizes: WAISTS.flatMap((waist) => [`W${waist}`, ...INSEAMS.map((inseam) => `${waist}x${inseam}`)]),
    },
    { name: "Shoes - US men's", sizes: range(6, 15, 0.5).map((size) => `US M ${size}`) },
    { name: "Shoes - US women's", sizes: range(5, 12, 0.5).map((size) => `US W ${size}`) },
    { name: "Kids", sizes: ["2T", "3T", "4T", "5T", ...range(6, 16, 2).map((size) => `Kids ${size}`)] },
];

export const PRESET_SIZES = SIZE_GROUPS.flatMap((group) => group.sizes);

const SIZE_GROUP_OF = new Map(SIZE_GROUPS.flatMap((group) => group.sizes.map((size) => [size, group.name] as const)));
const SIZE_ORDER = new Map(PRESET_SIZES.map((size, i) => [size.toLowerCase(), i]));

export function sizeGroup(size: string): string {
    return SIZE_GROUP_OF.get(size) ?? "Other";
}

// Preset sizes in their natural order (S before M before L), then anything custom A-Z
export function compareSizes(a: string, b: string): number {
    const orderA = SIZE_ORDER.get(a.trim().toLowerCase()) ?? Infinity;
    const orderB = SIZE_ORDER.get(b.trim().toLowerCase()) ?? Infinity;
    if (orderA !== orderB) return orderA - orderB;
    return a.localeCompare(b, undefined, { numeric: true });
}

export const COMMON_COLORS = [
    "Black", "White", "Gray", "Charcoal", "Navy", "Blue", "Light Blue", "Denim",
    "Red", "Burgundy", "Pink", "Purple", "Green", "Olive", "Yellow", "Orange",
    "Brown", "Tan", "Beige", "Cream", "Multicolor",
];

// Common colors plus the ones already on products, without case-only duplicates, so
// admins pick "Black" instead of adding "black" or "BLACK" next to it
export function colorSuggestions(usedColors: (string | null | undefined)[]): string[] {
    const suggestions = new Map<string, string>();

    for (const color of [...COMMON_COLORS, ...usedColors]) {
        const label = color?.trim();
        if (!label) continue;

        const key = label.toLowerCase();
        if (!suggestions.has(key)) suggestions.set(key, label);
    }

    return [...suggestions.values()];
}
