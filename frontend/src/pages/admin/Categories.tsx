import { useEffect, useRef, useState } from "react";
import { IconButton, TextField } from "@mui/material";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import AdminNav from "../../components/admin/AdminNav";
import ConfirmDeleteModal from "../../components/admin/ConfirmDeleteModal";
import AdminSnackbar, { type AdminNotice } from "../../components/admin/AdminSnackbar";
import { createCategory, deleteCategory, getCategories, reorderCategories, updateCategory, type Category } from "../../api/admin";
import { apiErrorMessage } from "../../api/errors";
import { useCategories } from "../../context/useCategories";

export default function AdminCategories() {

    const [categories, setCategories] = useState<Category[]>([]);
    const { refreshCategories } = useCategories();
    const [notice, setNotice] = useState<AdminNotice>(null);

    // Create form
    const [newName, setNewName] = useState("");
    const [newDescription, setNewDescription] = useState("");

    // Inline edit row
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editName, setEditName] = useState("");
    const [editDescription, setEditDescription] = useState("");

    const [pendingDelete, setPendingDelete] = useState<Category | null>(null);
    const [reordering, setReordering] = useState(false);
    const reorderInFlight = useRef(false);  // blocks clicks that land before the disabled state renders

    async function fetchCategories() {
        try {
            setCategories(await getCategories());

            // Keep the storefront nav in sync with admin changes
            refreshCategories();
        }
        catch (err) {
            setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to load categories") });
        }
    }

    useEffect(() => {
        getCategories().then(
            (data) => { setCategories(data); refreshCategories(); },
            (err) => setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to load categories") }),
        );
    }, [refreshCategories]);

    async function handleCreate() {
        try {
            await createCategory({ name: newName.trim(), description: newDescription.trim() || null });
            setNewName("");
            setNewDescription("");
            setNotice({ severity: "success", message: "Category created" });
            fetchCategories();
        }
        catch (err) {
            setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to create category") });
        }
    }

    function startEdit(category: Category) {
        setEditingId(category.category_id);
        setEditName(category.name);
        setEditDescription(category.description ?? "");
    }

    async function handleUpdate() {
        if (editingId === null) return;

        try {
            await updateCategory(editingId, { name: editName.trim(), description: editDescription.trim() || null });
            setEditingId(null);
            setNotice({ severity: "success", message: "Category updated" });
            fetchCategories();
        }
        catch (err) {
            setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to update category") });
        }
    }

    // Swap a category with its neighbour (direction -1 = up, 1 = down) and save the new order.
    // The arrows stay disabled until the save finishes, so the next move starts from the saved order
    async function handleMove(index: number, direction: -1 | 1) {
        const target = index + direction;
        if (reorderInFlight.current || target < 0 || target >= categories.length) return;

        const reordered = [...categories];
        [reordered[index], reordered[target]] = [reordered[target], reordered[index]];

        reorderInFlight.current = true;
        setReordering(true);
        try {
            setCategories(await reorderCategories(reordered.map((category) => category.category_id)));
            refreshCategories();
        }
        catch (err) {
            setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to reorder categories") });

            // The list may be out of date (e.g. another admin added a category), so reload it
            fetchCategories();
        }
        finally {
            reorderInFlight.current = false;
            setReordering(false);
        }
    }

    async function handleDelete() {
        if (!pendingDelete) return;

        try {
            await deleteCategory(pendingDelete.category_id);
            setNotice({ severity: "success", message: "Category deleted" });
            fetchCategories();
        }
        catch (err) {
            setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to delete category") });
        }
        finally {
            setPendingDelete(null);
        }
    }


    return (
        <>
        <AdminNav />

        <div className="p-4 md:p-10 flex flex-col gap-6">

            {/* Create Category */}
            <div className="flex flex-col gap-3">
                <h1 className="text-2xl md:text-4xl tracking-wider">CREATE NEW CATEGORY</h1>
                <div className="flex flex-wrap gap-2 items-center border rounded-lg p-2">
                    <TextField required label="Name" value={newName} onChange={(e) => setNewName(e.target.value)}/>
                    <TextField label="Description" className="flex-1" value={newDescription} onChange={(e) => setNewDescription(e.target.value)}/>
                    <button disabled={!newName.trim()} onClick={handleCreate} className="border rounded-full px-5 py-1 disabled:bg-gray-100 disabled:text-gray-400">Create</button>
                </div>
            </div>

            {/* Categories Table */}
            <div className="p-6 border rounded-lg bg-white shadow-xs flex flex-col gap-4">

                <div className="grid grid-cols-5 gap-4 text-sm font-semibold text-gray-500 border-b pb-2">
                    <div className="text-center tracking-wider">NAV ORDER</div>
                    <div className="text-center tracking-wider">CATEGORY ID</div>
                    <div className="text-center tracking-wider">NAME</div>
                    <div className="text-center tracking-wider">DESCRIPTION</div>
                    <div className="text-center tracking-wider">ACTIONS</div>
                </div>

                {categories.map((category, index) => (
                    <div key={category.category_id} className="grid grid-cols-5 gap-4 py-2 items-center">
                        <div className="flex justify-center items-center gap-1">
                            <IconButton size="small" aria-label={`Move ${category.name} up`} disabled={reordering || index === 0} onClick={() => handleMove(index, -1)}>
                                <KeyboardArrowUpIcon fontSize="small" />
                            </IconButton>
                            <IconButton size="small" aria-label={`Move ${category.name} down`} disabled={reordering || index === categories.length - 1} onClick={() => handleMove(index, 1)}>
                                <KeyboardArrowDownIcon fontSize="small" />
                            </IconButton>
                        </div>
                        <div className="text-center">{category.category_id}</div>

                        {editingId === category.category_id ? (
                            <>
                            <TextField size="small" label="Name" value={editName} onChange={(e) => setEditName(e.target.value)}/>
                            <TextField size="small" label="Description" value={editDescription} onChange={(e) => setEditDescription(e.target.value)}/>
                            <div className="flex justify-center gap-2">
                                <button onClick={() => setEditingId(null)} className="border rounded-[10px] px-6 py-1 hover:bg-gray-300">Cancel</button>
                                <button disabled={!editName.trim()} onClick={handleUpdate} className="border rounded-[10px] px-6 py-1 bg-green-300 hover:bg-green-400 disabled:bg-gray-100 disabled:text-gray-400">Save</button>
                            </div>
                            </>
                        ) : (
                            <>
                            <div className="text-center">{category.name}</div>
                            <div className="text-center">{category.description}</div>
                            <div className="flex justify-center gap-2">
                                <button onClick={() => startEdit(category)} className="border rounded-[10px] px-8 py-1 hover:bg-gray-300">Update</button>
                                <button onClick={() => setPendingDelete(category)} className="border rounded-[10px] px-8 py-1 bg-red-500 text-white hover:bg-red-600">Delete</button>
                            </div>
                            </>
                        )}
                    </div>
                ))}

            </div>
        </div>

        <ConfirmDeleteModal
            open={pendingDelete !== null}
            message={`Are you sure you want to delete the category "${pendingDelete?.name}"?`}
            onClose={() => setPendingDelete(null)}
            onConfirm={handleDelete}
        />

        <AdminSnackbar notice={notice} onClose={() => setNotice(null)} />
        </>
    );
}
