// The categories context and its hook, kept apart from CategoriesProvider so that file
// exports only a component (which React Fast Refresh needs)
import { createContext, useContext } from "react";
import type { Category } from "../api/categories";

interface CategoriesContextType {
    categories: Category[];
    loading: boolean;
    refreshCategories: () => Promise<void>;
}

export const CategoriesContext = createContext<CategoriesContextType | undefined>(undefined);

export const useCategories = () => {
    const context = useContext(CategoriesContext);
    if (!context) throw new Error("useCategories must be used within a CategoriesProvider");
    return context;
};
