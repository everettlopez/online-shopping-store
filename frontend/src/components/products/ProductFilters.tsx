import type { FilterOption, ProductFilterState, ProductSort } from "../../utils/productFilters";

interface ProductFiltersProps {
    filters: ProductFilterState;
    sizeOptions: FilterOption[];
    colorOptions: FilterOption[];
    canClear: boolean;
    onChange: (filters: ProductFilterState) => void;
    onClear: () => void;
    // In the phone drawer, which has its own title and frame
    inDrawer?: boolean;
}

const SORT_OPTIONS: { value: ProductSort; label: string }[] = [
    { value: "featured", label: "Featured" },
    { value: "newest", label: "Newest" },
    { value: "price-asc", label: "Price: low to high" },
    { value: "price-desc", label: "Price: high to low" },
];

export default function ProductFilters({ filters, sizeOptions, colorOptions, canClear, onChange, onClear, inDrawer = false }: ProductFiltersProps) {

    function toggle(group: "sizes" | "colors", value: string) {
        const selected = filters[group];
        onChange({
            ...filters,
            [group]: selected.includes(value) ? selected.filter((v) => v !== value) : [...selected, value],
        });
    }

    function checkboxGroup(title: string, group: "sizes" | "colors", options: FilterOption[]) {
        if (options.length === 0) return null;

        return (
            <fieldset className="flex flex-col gap-2">
                <legend className="text-sm font-semibold tracking-widest mb-2">{title}</legend>
                {options.map((option) => (
                    <label key={option.value} className="flex items-center gap-2 text-sm tracking-wider cursor-pointer">
                        <input
                            type="checkbox"
                            checked={filters[group].includes(option.value)}
                            onChange={() => toggle(group, option.value)}
                        />
                        {option.label.toUpperCase()}
                    </label>
                ))}
            </fieldset>
        );
    }

    return (
        <aside className={inDrawer ? "flex flex-col gap-6" : "hidden md:flex border rounded-2xl flex-col gap-6 p-6 w-60 shrink-0 self-start"}>
            <div className={`flex items-center ${inDrawer ? "justify-end" : "justify-between"}`}>
                {!inDrawer && <h2 className="text-lg tracking-widest">FILTER</h2>}
                <button
                    onClick={onClear}
                    disabled={!canClear}
                    className="text-xs tracking-wider underline disabled:no-underline disabled:text-gray-300"
                >
                    CLEAR
                </button>
            </div>

            <label className="flex flex-col gap-2">
                <span className="text-sm font-semibold tracking-widest">SORT BY</span>
                <select
                    value={filters.sort}
                    onChange={(e) => onChange({ ...filters, sort: e.target.value as ProductSort })}
                    className="border rounded-lg px-2 py-1 text-sm"
                >
                    {SORT_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                </select>
            </label>

            {checkboxGroup("SIZE", "sizes", sizeOptions)}
            {checkboxGroup("COLOR", "colors", colorOptions)}

            <fieldset className="flex flex-col gap-2">
                <legend className="text-sm font-semibold tracking-widest mb-2">PRICE</legend>
                <div className="flex items-center gap-2">
                    <input
                        type="number"
                        min={0}
                        placeholder="Min"
                        aria-label="Minimum price"
                        value={filters.minPrice}
                        onChange={(e) => onChange({ ...filters, minPrice: e.target.value })}
                        className="border rounded-lg px-2 py-1 text-sm w-full"
                    />
                    <span className="text-gray-400">–</span>
                    <input
                        type="number"
                        min={0}
                        placeholder="Max"
                        aria-label="Maximum price"
                        value={filters.maxPrice}
                        onChange={(e) => onChange({ ...filters, maxPrice: e.target.value })}
                        className="border rounded-lg px-2 py-1 text-sm w-full"
                    />
                </div>
            </fieldset>
        </aside>
    );
}
