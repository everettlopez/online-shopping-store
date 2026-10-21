import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getStoreCategories, type Category } from "../api/categories";

interface CategoriesContextType {
    categories: Category[];
    loading: boolean;
    refreshCategories: () => Promise<void>;
}

const CategoriesContext = createContext<CategoriesContextType | undefined>(undefined);

export const CategoriesProvider = ({ children }: { children: React.ReactNode }) => {
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);

    const refreshCategories = useCallback(async () => {
        try {
            setCategories(await getStoreCategories());
        } catch (err) {
            console.error("Failed to fetch categories: ", err);
        }
    }, []);

    useEffect(() => {
        getStoreCategories()
            .then(setCategories)
            .catch((err) => console.error("Failed to fetch categories: ", err))
            .finally(() => setLoading(false));
    }, []);

    return (
        <CategoriesContext.Provider value={{ categories, loading, refreshCategories }}>
            {children}
        </CategoriesContext.Provider>
    );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useCategories = () => {
    const context = useContext(CategoriesContext);
    if (!context) throw new Error("useCategories must be used within a CategoriesProvider");
    return context;
};
