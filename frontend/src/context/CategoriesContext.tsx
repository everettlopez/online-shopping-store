import { useCallback, useEffect, useState } from "react";
import { getStoreCategories, type Category } from "../api/categories";
import { CategoriesContext } from "./useCategories";

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
